class _Acc:
    def device_name(self, *a): return 'cpu'
    def current_device_name(self): return 'cpu'
    def is_available(self): return False
    def communication_backend_name(self): return 'gloo'
def get_accelerator(): return _Acc()
