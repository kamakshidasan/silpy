class TreeChecker:
    @staticmethod
    def check_value(*allowed_values):
        def check(value):
            return value in allowed_values
        return check

    is_merge   = check_value('join', 'split')
    is_join    = check_value('join')
    is_split   = check_value('split')

def __getattr__(name):
    return getattr(TreeChecker, name)
