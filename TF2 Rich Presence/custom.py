# Copyright (C) 2019 Kataiser & https://github.com/Kataiser/tf2-rich-presence/contributors
# https://github.com/Kataiser/tf2-rich-presence/blob/master/LICENSE

# Add some custom functionality to TF2 Rich Presence if you'd like
# Quite limited but someone may find a use it (I know I have)
# Also you can replace a .pyd file here with a .py of the same name (sans .cp37-win32) and it'll import

import logger
import main


class TF2RPCustom:
    def __init__(self):
        pass

    def before_loop(self, app: main.TF2RichPresense):
        # app.log.debug("Performing custom.before_loop()")
        pass

    # after TF2RichPresense.activity is finalized but before it's displayed or sent to Discord
    def loop_middle(self, app: main.TF2RichPresense):
        # app.log.debug("Performing custom.loop_middle()")
        pass

    def after_loop(self, app: main.TF2RichPresense):
        # app.log.debug("Performing custom.after_loop()")
        pass


if __name__ == '__main__':
    test_app = main.TF2RichPresense(logger.Log())
    test_TF2RPCustom = TF2RPCustom()

    test_TF2RPCustom.before_loop(test_app)
    test_TF2RPCustom.loop_middle(test_app)
    test_TF2RPCustom.after_loop(test_app)
