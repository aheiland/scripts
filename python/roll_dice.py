import weechat
from random import randint, seed
import argparse
import re

weechat.register("roll_dice", "Andreas Rau", "1.0.0", "GPL3", "roll dice script", "", "")
seed()
def get_count_and_faces(args):
    try:
        if len(args) < 1:
            count = 1
            faces = 6
        elif args.isdigit():
            count = int(args)
            faces = 6
        else:
            [count, faces] = [int(x) for x in args.split("d")][0:2]
    except:
        count = 1
        faces = 6
    return [count, faces]

def roll(count: int, faces: int):
    return sum([randint(1, faces) for _ in range(0, count)])

def arg_dice_type(arg_value):
    pat = re.compile("\d+(d\d+)?")
    if not pat.match(arg_value):
        raise argparse.ArgumentTypeError
    return arg_value

def prepare_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('dice', type=arg_dice_type)
    parser.add_argument('--advantage', action='store_true')
    parser.add_argument('--disadvantage', action='store_true')
    parser.add_argument('--against', type=int)
    parser.add_argument('--modifier', type=int, default=0)
    return parser.parse_args(args.split())

def first(arr: list):
    return arr[0]

def roll_modifier(modifier):
    if modifier == 0:
        return ""
    if modifier < 0:
        return " ({})".format(modifier)
    if modifier > 0:
        return " (+{})".format(modifier)

def roll_critical(count, faces, roll_result):
    if faces < 3:
        return ""
    if count == roll_result:
        return " with a natural 1"
    if (count * faces) == roll_result:
        return " with a natural {}".format(faces)
    return ""

def roll_normal(count, faces, mode, roll_result, modifier):
    modified = roll_modifier(modifier)
    critical = roll_critical(count, faces, roll_result)
    return " rolled {} {}-sided dice with {} and got: {} {}{}".format(
            count,
            faces,
            "advantage" if mode == 1 else "disadvantage",
            max([1, roll_result + modifier]),
            modified,
            critical
        )\
        if mode in (1,2)\
        else\
        " rolled {} {}-sided dice and got: {} {}{}".format(
            count,
            faces,
            max([1, roll_result + modifier]),
            modified,
            critical
        )

def roll_against(count, faces, roll_result, against, modifier):
    successful = against <= max([1, roll_result + modifier])
    critical = roll_critical(count, faces, roll_result)
    return " rolled against {} and {}{}".format(
            against,
            "was successful" if successful else "failed",
            critical
        )

def roll_dice(dice, advantage, disadvantage, against, modifier):
    [count, faces] = get_count_and_faces(dice)
    mode = advantage + (disadvantage << 1)
    roll_result = ((first,max,min,first)[mode])([roll(count, faces), roll(count, faces)])
    return roll_against(count, faces, roll_result, against, modifier)\
        if against is not None\
        else roll_normal(count, faces, mode, roll_result, modifier)

def roll_dice_cb(_, buffer, args):
    diceArgs = prepare_args(args)
    text = roll_dice(
        diceArgs.dice,
        diceArgs.advantage,
        diceArgs.disadvantage,
        diceArgs.against,
        diceArgs.modifier
    )
    [server, channel] = weechat.buffer_get_string(buffer, 'name').split(".",1)
    send = "{};{};{};;/me {}".format(
        server,
        channel,
        'priority_low',
        text
    )
    weechat.hook_signal_send(
        "irc_input_send",
        weechat.WEECHAT_HOOK_SIGNAL_STRING,
        send
    )
    return weechat.WEECHAT_RC_OK

hook = weechat.hook_command(
    "roll",
    "Rolles dice",
    "[--advantage] [--disadvantage] [--against int] [--modifier [+|-]int] <int>d<int>",
    "Count and faces of the dice",
    "d dice",
    "roll_dice_cb",
    ""
)
