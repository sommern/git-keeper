
from gkeeprobot.dectorators import polling
import sys
import pwd


@polling
def user_exists(user):
    try:
        pwd.getpwnam(user)
        return True
    except:
        return False


print(user_exists(sys.argv[1]))
