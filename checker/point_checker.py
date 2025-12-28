class PointChecker:
    @staticmethod
    def check_type(*types):
        def check(self):
            return self.type in types
        return check

    is_maximum       = check_type('maximum')
    is_minimum       = check_type('minimum')
    is_join          = check_type('join')
    is_split         = check_type('split')
    is_both          = check_type('both')
    is_saddle        = check_type('join', 'split', 'both')
    is_join_or_both  = check_type('join', 'both')
    is_split_or_both = check_type('split', 'both')
    is_extremum      = check_type('maximum', 'minimum')
    is_regular       = check_type('regular')
