import paste.script.command as pscmd


class AddAdministrator(pscmd.Command):
    # Parser configuration
    summary = "add an administrative user"
    usage = ""

    parser = pscmd.Command.standard_parser(verbose=False)

    min_args = 0
    max_args = 0

    def command(self):
        from compstack.auth.helpers import add_administrative_user
        add_administrative_user(allow_profile_defaults=False)
