# Memory mapped OpenFOAM file

The final example is to read an OpenFOAM file as a memory mapped array. There are some details that need attention.

```python
import mmap
import numpy as np
from byteparsing import parse_bytes
from byteparsing.openfoam import foam_file

f = Path("pipeFlow/1.0/U").open(mode="r+b")
with mmap.mmap(f.fileno(), 0) as mm:
  content = parse_bytes(foam_file, mm)
  result = content["data"]["internalField"]

  <<do work ...>>

  del result
  del content
```

The content is returned in the form of a nested dictionary. The `"internalField"` item is a name that one often finds in OpenFOAM files. The `result` object is a Numpy `ndarray` created using a `np.frombuffer` call. Any mutations to the Numpy array are directly reflected on the disk. This means that accessing large amounts of data can be extremely efficient in terms of memory footprint.

The final two `del` statements are necessary to ensure that no reference to the memory-mapped data outlives the memory map itself, which is closed as soon as we leave the `with mmap ...` context.