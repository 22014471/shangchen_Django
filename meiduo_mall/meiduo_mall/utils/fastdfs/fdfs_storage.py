from fdfs_client.client import Fdfs_client
from django.core.files.storage import Storage
from django.conf import settings
from django.utils.deconstruct import deconstructible


@deconstructible
class FastDFSStorage(Storage):
    """自定义django文件存储系统"""

    def __init__(self):  # , base_url=None, client_conf=None
        if not hasattr(settings, 'FDFS_CLIENT_CONF'):
            raise Exception("lack config:FDFS_CLIENT_CONF")
        self.client_conf = getattr(settings, 'FDFS_CLIENT_CONF')
        if not hasattr(settings, 'FDFS_URL'):
            raise Exception("lack config:FDFS_URL")
        self.base_url = getattr(settings, 'FDFS_URL')
        self.client = Fdfs_client(self.client_conf)

    def _open(self):
        pass

    def _save(self, name, content):
        ext_name = name.split(".")[-1]
        ret = self.client.upload_by_buffer(content.read(), file_ext_name=ext_name)
        if ret.get("Status") != 'Upload successed.':
            raise Exception('upload file failed')
        filename = ret.get("Remote file_id")
        return filename

    def url(self, name):
        return self.base_url + name

    def exists(self, name):
        return False
