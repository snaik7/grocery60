import logging
from grocery60_be import settings
import json 
import time

class AuditMiddleware(object):
    
    def __init__(self, get_response):
        self.audit_text = {}
        self.start_time = ''
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        start_time = time.time()
        self.start_time  = start_time
        self.audit_text['start_time'] = start_time
        if request.headers.get('order_id'):
            self.audit_text['order_id'] = request.headers.get('order_id')
        if request.headers.get('user_id'):
            self.audit_text['user_id'] = request.headers.get('user_id')
        if request.headers.get('cart_id'):
            self.audit_text['cart_id'] = request.headers.get('cart_id')
        if request.headers.get('action'):
            self.audit_text['action'] = request.headers.get('action')
        self.audit_text['START'] = 'TRUE'
        PROJECT = settings.PROJECT

        # reference code https://cloud.google.com/run/docs/logging#run_manual_logging-python
        # Build structured log messages as an object.
        global_log_fields = {}

        # Add log correlation to nest all log messages
        # beneath request log in Log Viewer.
        trace_header = request.headers.get('X-Cloud-Trace-Context')

        if trace_header and PROJECT:
            trace = trace_header.split('/')
            global_log_fields['logging.googleapis.com/trace'] = (
                f"projects/{PROJECT}/traces/{trace[0]}")

        # Complete a structured log entry.
        entry = dict(severity='INFO',
                     message=self.audit_text,
                     # Log viewer accesses 'component' as jsonPayload.component'.
                     component='audit',
                     **global_log_fields)
        print('p',json.dumps(entry))
        logging.info(json.dumps(entry))
        return None

    def process_template_response(self, request, response):
        if request.headers.get('action'):
            self.audit_text['action'] = request.headers.get('action')
        self.audit_text['END'] = 'TRUE'
        end_time = time.time()
        self.audit_text['end_time'] = end_time
        self.audit_text['time_elapsed'] = end_time - self.start_time
        PROJECT = settings.PROJECT

        # Build structured log messages as an object.
        global_log_fields = {}

        # Add log correlation to nest all log messages
        # beneath request log in Log Viewer.
        trace_header = request.headers.get('X-Cloud-Trace-Context')

        if trace_header and PROJECT:
            trace = trace_header.split('/')
            global_log_fields['logging.googleapis.com/trace'] = (
                f"projects/{PROJECT}/traces/{trace[0]}")

        # Complete a structured log entry.
        entry = dict(severity='INFO',
                     message=self.audit_text,
                     # Log viewer accesses 'component' as jsonPayload.component'.
                     component='audit',
                     **global_log_fields)

        print('p',json.dumps(entry))
        logging.info(json.dumps(entry))
        return response