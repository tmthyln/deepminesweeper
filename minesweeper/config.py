import argparse
from dataclasses import dataclass, field
import re

from typing import Union, Any, List, Set, Dict, TypeVar, Sequence

import minesweeper


class Group:
    _group: str = 'None'
    _groups: Set[str] = set()
    
    @classmethod
    def current_group(cls) -> str:
        return cls._group
    
    @classmethod
    def all_groups(cls) -> List[str]:
        return list(cls._groups)
    
    def __init__(self, group_name: str):
        self._group = group_name
        Group._groups.add(group_name)
    
    def __enter__(self):
        Group._group = self._group
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        Group._group = 'None'


T = TypeVar('T')


@dataclass
class ConfigItem:
    default: T = None
    metavar: Union[str, Sequence[str]] = None
    action: Union[str, argparse.Action] = None
    type: type = None
    nargs: int = None
    choices: Sequence[T] = None
    help: str = None
    group: str = field(default_factory=Group.current_group)
    
    _value = None
    
    @property
    def params(self) -> Dict[str, Any]:
        def condition(key, val):
            return not key.startswith('_') and key != 'group' and val is not None
        
        return {key: val for key, val in self.__dict__.items() if condition(key, val)}
    
    @property
    def value(self) -> Any:
        return self.default if self._value is None else self._value
    
    @value.setter
    def value(self, new_value):
        self._value = new_value


class ConfigMeta(type):
    
    def __getattribute__(cls, name):
        ret_val = type.__getattribute__(cls, name)
        return ret_val.value if isinstance(ret_val, ConfigItem) else ret_val
    
    @property
    def params(cls):
        return {name: value for name, value in cls.__dict__.items() if not name.startswith('_')}

    @property
    def arg_parser(cls):
        parser = argparse.ArgumentParser('Minesweeper')
        parser.add_argument('--version', action='version', version=minesweeper.VERSION)
    
        argument_groups = {group_name: parser.add_argument_group(group_name) for group_name in Group.all_groups()}
    
        for param_name, config_item in cls.params.items():
            argument_groups[config_item.group].add_argument(f'--{param_name.replace("_", "-")}', **config_item.params)
    
        return parser
    
    def update_from_dict(cls, param_dict):
        for param_name, value in param_dict.items():
            try:
                config_item = type.__getattribute__(cls, param_name)
            except AttributeError:
                config_item = ConfigItem()
            
            if config_item.type is not None:
                # convert value as needed
                pass
            
            config_item.value = value
            setattr(cls, param_name, config_item)
    
    def update_from_cfg(cls, filename: str):
        assert filename.endswith('.cfg')

        cfg_line_pattern = re.compile(r'^(\w+)=(.+)$')
        with open(filename, 'r') as f:
            args = {matched[1]: matched[2] for line in f if (matched := cfg_line_pattern.match(line))}
        
        cls.update_from_dict(args)
    
    def update_from_yaml(cls, filename: str):
        assert filename.endswith('.yml') or filename.endswith('.yaml')
        
        pass  # FEAT allow updates from a complex, .yaml config file
        
    def update_from_args(cls, *args):
        namespace, unknown_args = cls.arg_parser.parse_known_args(*args)
        known_args = {key: val for key, val in namespace.__dict__.items() if not key.startswith('_')}
        
        cls.update_from_dict(known_args)
        return unknown_args


class Config(metaclass=ConfigMeta):
    pass


class DefaultConfig(Config):
    with Group('resources'):
        res_dir = ConfigItem(
                default='res',
                metavar='RESOURCE_DIRECTORY',
                help='root directory for all resources')
        favicon_file = ConfigItem(
                default='favicon.png',
                metavar='FILENAME')
        hidden_cell_file = ConfigItem(
                default='hidden_cell.png',
                metavar='FILENAME')
        open_cell_file = ConfigItem(
                default='open_cell.png',
                metavar='FILENAME')
    
    with Group('aesthetic'):
        window_title = ConfigItem(
                default='Minesweeper')
        bg_color = ConfigItem(
                default=(0, 120, 0),
                type=int,
                nargs=3,
                metavar=tuple('RGB'))
    
    with Group('windowing'):
        window_size = ConfigItem(
                default=(1280, 780),
                type=int,
                nargs=2,
                metavar=('WIDTH', 'HEIGHT'))
        cell_size = ConfigItem(
                default=(32, 32),
                type=int,
                nargs=2,
                metavar=('WIDTH', 'HEIGHT'))
        fps = ConfigItem(
                default=60,
                type=int)
    
    with Group('gameplay'):
        good_first_select = ConfigItem(
                action='store_true',
                help='guarantee that the first select will be on an empty cell (no neighbors)')
        end_on_first_mine = ConfigItem(
                default=True,
                help='whether to end a game on the first mine selected (see also: forgiveness)')
        forgiveness = ConfigItem(
                default=5,
                metavar='MINES',
                type=Union[int, float],
                help='number of mines to allow before ending the game, if not ending on first mine')
        agent = ConfigItem(
                default=None,
                choices=minesweeper.AGENT_REGISTRY.keys())
        shape = ConfigItem(
                default='square',
                choices=['square'],
                help='shape of the cell')  # TODO add support for other regular polygons
    
    with Group('controls'):
        double_click_time = ConfigItem(
                default=400,
                type=int,
                metavar='TIME_MS')
        click_to_flag = ConfigItem(
                default=True)
        use_super_chord = ConfigItem(
                action='store_true')
        
    with Group('logging'):
        log_dir = ConfigItem(
                default='runs',
                metavar='LOG_DIRECTORY',
                help='root directory for all log files created')
        save_board_runs = ConfigItem(
                default=True,
                help='whether to save the board configurations for each game played')
