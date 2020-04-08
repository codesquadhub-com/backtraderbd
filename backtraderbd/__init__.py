import codecs
import os

__version__ = codecs.open(os.path.join(os.path.dirname(__file__), 'VERSION.txt')).read()
__author__ = 'Raisul Islam'


from backtraderbd.libs.models import (get_store, get_library,
                                        create_library, get_or_create_library,
                                        drop_library, get_bd_stocks,
                                        save_training_params)
