from colorama import Fore, Style


def red(string):
    print(Fore.RED + string + Style.RESET_ALL)


def green(string):
    print(Fore.GREEN + string + Style.RESET_ALL)


def cyan(string):
    print(Fore.CYAN + string + Style.RESET_ALL)


def bright(string):
    print(Style.BRIGHT + string + Style.RESET_ALL)
