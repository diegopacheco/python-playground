from terminaltexteffects.effects.effect_burn import Burn
from terminaltexteffects.effects.effect_expand import Expand
from terminaltexteffects.effects.effect_waves import Waves

import subprocess

def get_ls_output():
    command = ['ls', '-lsa']
    result = subprocess.run(command, stdout=subprocess.PIPE)
    return result.stdout.decode('utf-8')

def run_effect(effect):
    with effect.terminal_output() as terminal:
        for frame in effect:
            terminal.print(frame)

run_effect(Burn(get_ls_output()))
run_effect(Expand(get_ls_output()))
run_effect(Waves(get_ls_output()))