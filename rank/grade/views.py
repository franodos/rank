import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django_redis import get_redis_connection
from grade.serializers import ClientSerializer
from django.db.models.aggregates import Max
from django.db import transaction
from grade.models import Client
from django.conf import settings

logger = logging.getLogger("rank")


class RanKCacheError(Exception):
    def __init__(self, msg=None):
        if msg is None:
            msg = "Rank list Cache error"
        super().__init__(msg)


def init_rank() -> bool:
    """使用SortedSet类型初始化排行榜，如果排行榜已经存在，直接返回，否则进行初始化"""
    try:
        con = get_redis_connection("default")
        res = con.exists(settings.RANK_KEY)
        if res:
            return True
        res = Client.objects.values("number").annotate(Max("grade"))
        rank_list = [(item.get("number"), item.get("grade__max")) for item in res]
        con = get_redis_connection("default")
        con.zadd(settings.RANK_KEY, dict(rank_list))
        return True
    except Exception as exc:
        logger.error("init rank list error:{0}".format(exc), exc_info=True)
        return False


class ClientView(APIView):
    @transaction.atomic
    def post(self, request, format=None):
        """上传客户端号和分数"""
        sid = transaction.savepoint()
        try:
            serializer = ClientSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                for _ in range(3):
                    res = self.set_client_grade(serializer.data.get("number"), serializer.data.get("grade"))
                    if res is True:
                        break
                else:
                    raise RanKCacheError()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error("insert data fail:{0}".format(e), exc_info=True)
            transaction.savepoint_rollback(sid)
            return Response({"detail": "insert data fail:{0}".format(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def set_client_grade(client, grade) -> bool:
        """
        使用乐观锁更新redis中的分数排行榜
        将新插入的客户端分数保存到SortedSet: 如果新分数为最大值，保存，否则不保存
        """
        try:
            # 初始化排行榜
            res = init_rank()
            if res is False:
                raise False

            rank_key = settings.RANK_KEY
            client_key = "client{0}".format(client)
            con = get_redis_connection("default")
            con.watch(client_key)
            old_grade = con.zscore(settings.RANK_KEY, client)
            old_grade = -1 if old_grade is None else old_grade
            if old_grade < grade:
                pipe = con.pipeline(transaction=True)
                pipe.incr(client_key)
                pipe.zadd(rank_key, {client: grade})
                pipe.execute()
            return True
        except Exception as exc:
            logger.error("set client grade in redis error:{0}".format(exc), exc_info=True)
            return False


class RankView(APIView):
    def get(self, request, format=None):
        """获取排行榜"""
        try:
            start = int(request.GET.get("start") or 0)
            stop = int(request.GET.get("stop") or -1)
            number = request.GET.get("number")
            if not number:
                return Response({"detail": "don't pass client number"}, status=status.HTTP_400_BAD_REQUEST)
            number = int(number)
        except Exception as exc:
            return Response({"detail": "params error: {0}".format(exc)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            res = init_rank()
            if res is False:
                return Response({"detail": "can't get rank list"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            client_key = "client{0}".format(number)
            con = get_redis_connection("default")
            con.watch(client_key)
            pipe = con.pipeline(transaction=True)
            pipe.incr(client_key)
            pipe.zrevrange(settings.RANK_KEY, start, stop, withscores=True) or []
            pipe.zscore(settings.RANK_KEY, number)
            res = pipe.execute()
            _, rank_list, score = res
            rank_list = [(int(key.decode("utf-8")), int(value)) for key, value in rank_list]
            if score:
                rank_list.append((number, int(score)))
            return Response(rank_list)
        except Exception as exc:
            logger.error("get rank list fail:{0}".format(exc), exc_info=True)
            return Response({"detail": "get rank list fail"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
