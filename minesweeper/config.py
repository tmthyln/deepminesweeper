import argparse
from dataclasses import dataclass, field
import re

from typing import Union, Any, List, Set, Dict, TypeVar, Sequence

import minesweeper


class GroupMeta(type):
    _group: List[str] = []
    _groups: Set[str] = set()
    
    @property
    def current_group(cls):
        return '.'.join(cls._group)
    
    @property
    def all_groups(cls):
        return list(cls._groups)
    
    def subgroup(cls, local_name):
        cls._group.append(local_name)
        cls._groups.add(cls.current_group)
        
    def ungroup(cls):
        cls._group.pop()


class Group(metaclass=GroupMeta):
    
    def __init__(self, local_name: str):
        self._local_name = local_name
    
    def __enter__(self):
        Group.subgroup(self._local_name)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        Group.ungroup()


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
    group: str = field(default_factory=lambda: Group.current_group)
    
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


class ColorConfigItem(ConfigItem):
    def __init__(self, r, g, b, **kwargs):
        super().__init__(default=(r, g, b), type=int, nargs=3, metavar=tuple('RGB'), **kwargs)


class FileConfigItem(ConfigItem):
    def __init__(self, filename, **kwargs):
        super().__init__(default=filename, metavar='FILENAME', **kwargs)
        
        
class SizeConfigItem(ConfigItem):
    def __init__(self, width, height, **kwargs):
        super().__init__(default=(width, height), type=int, nargs=2, metavar=('WIDTH', 'HEIGHT'), **kwargs)


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
    
        argument_groups = {group_name: parser.add_argument_group(group_name) for group_name in Group.all_groups}
    
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
    # TODO allow dicts or values to be assigned to the config (converted to ConfigItem's)

    with Group('resources'):
        res_dir = ConfigItem(
                default='res',
                metavar='RESOURCE_DIRECTORY',
                help='root directory for all resources')
        favicon_file = FileConfigItem('favicon.png')
        hidden_cell_file = FileConfigItem('hidden_cell.png')
        open_cell_file = FileConfigItem('open_cell.png')
    
    with Group('aesthetic'):
        window_title = ConfigItem(default='Minesweeper')
        bg_color = ColorConfigItem(255, 255, 255)
        num_color = ColorConfigItem(0, 0, 0)
        
        with Group('statusbar'):
            status_bg_color = ColorConfigItem(0, 120, 0)
    
    with Group('windowing'):
        window_size = SizeConfigItem(1280, 780)
        cell_size = SizeConfigItem(32, 32)
        fps = ConfigItem(default=60, type=int)
    
    with Group('gameplay'):
        good_first_select = ConfigItem(
                action='store_true',
                help='guarantee that the first select will be on an empty cell (no neighbors)')
        forgiveness = ConfigItem(
                default=0,
                metavar='MINES',
                type=Union[int, float],
                help='number of mines to allow before ending the game')
        board = ConfigItem(
                default='square',
                choices=minesweeper.BOARD_REGISTRY.keys())
        agent = ConfigItem(
                default=None,
                choices=minesweeper.AGENT_REGISTRY.keys())
    
    with Group('controls'):
        double_click_time = ConfigItem(
                default=400,
                type=int,
                metavar='TIME_MS')
        click_to_flag = ConfigItem(default=True)
        superchord = ConfigItem(
                default='none',
                choices=['none', 'auto', 'keyup'])
        
    with Group('logging'):
        log_dir = ConfigItem(
                default='runs',
                metavar='LOG_DIRECTORY',
                help='root directory for all log files created')
        save_board_runs = ConfigItem(
                default=True,
                help='whether to save the board configurations for each game played')
