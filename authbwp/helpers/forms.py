from savalidation import ValidationError

from plugstack.common.lib.forms import Form as CommonForm

class Form(CommonForm):
    def __init__(self, name=None, **kwargs):
        CommonForm.__init__(self, name, **kwargs)
        self.add_handler(exc_type=ValidationError, callback=self.handle_validation_error)

    def handle_validation_error(self, exc):
        for inst in exc.invalid_instances:
            self.add_field_errors(inst.validation_errors)
        return True
