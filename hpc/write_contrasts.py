import numpy as np
import json
import sys
import os

sys.path.append(os.path.join(os.environ.get('HOMEDIR')))

from utils import utils

results = {}
for task in ['stopsignal', 'taskswitch', 'scap', 'bart', 'pamret']:
    contrasts = utils.create_contrasts(task)
    results[task] = [x[0] for x in contrasts]

contrastfile = os.path.join(os.environ.get('HOMEDIR'),"utils/contrasts.json")
with open(contrastfile,'w') as fp:
    json.dump(results,fp,sort_keys=True,indent=4)
