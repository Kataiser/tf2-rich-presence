import detect_system_language
import updater
import welcomer


def launch(welcome_version):
    # TODO: have a log and pass it into each of these
    welcomer.welcome(welcome_version)
    detect_system_language.detect()
    updater.run()


if __name__ == '__main__':
    launch(0)
