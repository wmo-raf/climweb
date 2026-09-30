from allauth.account.adapter import DefaultAccountAdapter


class NoSignupAccountAdapter(DefaultAccountAdapter):
    """Close allauth's public sign-up page (/auth/signup/).

    Accounts are created by administrators in the CMS. allauth itself stays
    installed because geomanager uses its password-reset emails, whose links
    point at /auth/.
    """

    def is_open_for_signup(self, request):
        return False
