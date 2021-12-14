import os
import inspect
import pickle

class Helper(object):
    '''
    This class provides helper functions such as:
    - saving/loading results
    -...
    '''

    def get_file_name(self,BT_params_fixed):
        asset=BT_params_fixed['asset']
        filename = BT_params_fixed['strategyName'] + '_' + asset + '_' \
                   + str(BT_params_fixed['interval']) + '_' + str(BT_params_fixed['fromdate'])[0:10] + '_' + str(
                    BT_params_fixed['todate'])[0:10] + '_#1'
        current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        while True:
            filepath_name = current_dir + '\\results\\' + filename + '.dat'
            if os.path.isfile(filepath_name):
                # file already existing
                indexing_idx = filename.index('#')
                file_count_idx = int(filename[indexing_idx + 1:len(filename)])
                filename = filename[0:indexing_idx + 1] + str(file_count_idx + 1)
            else:
                break
        return filename

    def load_results(self, filename):
        current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        filepath = current_dir + '\\results\\' + filename + '.dat'
        file = open(filepath, 'rb')
        object_file = pickle.load(file)
        return object_file

    def save_results(self, result, BT_params_fixed):
        filename = self.get_file_name(BT_params_fixed=BT_params_fixed)
        with open('results/' + str(filename) + '.dat', 'wb') as f:
            pickle.dump(result, f)
        return filename