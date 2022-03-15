import sys
import logging
import re

print("info is a %s." % (type(logging.info)))

# 'logging' isn't a class, thought logging.Logger is. Make sure this can
# patch onto that correctly.

def new_info(msg:str, *args, **kwargs):
    """Allow setting -v level like most *nix commands, and making headings,
    without having to use different parameters (though you *can*...).
    You can either pass these like this:
        logging.info("Something happened.", heading=True, level=2)
    Or pack them into prefixes on the message itself (this is so you can
    use exactly the logging() parameters, and therefore cut this out without
    having to change anything but your import):
        logging.info("====2:Something happened.")
    You need 4 or more "=" to generate a heading line before the message.
    The level number comes after the "=" (if any), and must have a colon following.
    If you're using this package, those prefixes get removed. They also take
    priority over the keyword parameters (if any).
    This automatically adds a newline at end of message unless already there.
    """
    # Set the defaults
    level = 0
    heading = False
    
    # Handle keyword args
    if "level" in kwargs:
        level = kwargs["level"]
        del kwargs["level"]
    if "heading" in kwargs:
        heading = kwargs["heading"]
        del kwargs["heading"]
    
    # Handle prefixed syntax on the message
    mat = re.match(r"(====+)?(\d+:)?(.*)", msg)
    if (mat):
        heading = bool(mat.group(1))
        level = int(mat.group(2)[0:-1])
        msg = mat.group(3)
    
    # Ok, now format and issue the message (or not).
    if (logging.verbose < level): return
    if (heading): msg = "\n%s\n%s" % ("=" * 79, msg)
    if (not msg.endswith("\n")): msg += "\n"
    return logging.original_info(msg, *args, **kwargs)
        
def setVerbose(level:int=0):
    assert isinstance(level, int)
    logging.verbose = level
    
def getVerbose():
    return logging.verbose

def fatal(msg:str, *args, **kwargs):
    logging.critical(msg, *args, **kwargs)
    sys.exit()
    
    
# Monkey-patch all of that into the logging package.
#
logging.verbose = 0
logging.setVerbose = setVerbose
logging.getVerbose = getVerbose

logging.original_info = logging.info
logging.info = new_info
logging.fatal = fatal