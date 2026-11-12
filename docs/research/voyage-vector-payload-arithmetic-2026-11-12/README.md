# Vector payload arithmetic

Version: 1.0.0. Observed: 2026-11-12 UTC.

This firsthand, synthetic serialization check reproduces raw vector payload
arithmetic. It uses Python's standard library and makes no network request.
It does not measure a Voyage model, retrieval quality, an Atlas index, RAM,
latency, retained full-fidelity storage or a bill.

| Assumed representation | Raw payload calculation | Verified bytes |
| --- | --- | ---: |
| 2,048 float32 coordinates | 2,048 × 32 bits ÷ 8 | 8,192 |
| 1,024 int8 coordinates | 1,024 × 8 bits ÷ 8 | 1,024 |
| 1,024 logical binary dimensions | 1,024 bits ÷ 8 | 128 |
| 512 logical binary dimensions | 512 bits ÷ 8 | 64 |

Under these assumptions, changing both dimension count and precision from
2,048 float32 coordinates to 1,024 int8 coordinates reduces raw coordinate
payload by exactly eightfold: 8,192 ÷ 1,024 = 8. The packed binary array lengths
above describe bytes, while the logical dimension counts remain 1,024 and 512.
These calculations exclude container metadata, headers, serialization overhead,
database and search indexes, retained representations and operational costs.

Run from this directory:

```sh
python3 verify_payload.py --output results.json
```

The script fixes standard type sizes and byte order, serializes synthetic
float32 and int8 values, and checks their complete round trips. It also packs
synthetic bits, checks every packed byte and reconstructs every logical bit.
The output records payload hashes so the result can be reproduced exactly.
[results.json](results.json) records the actual successful run.

API behavior is a separate source question. Voyage's primary documentation
lists the supported [model dimensions and output data types](https://docs.voyageai.com/docs/embeddings)
and describes [binary packing](https://docs.voyageai.com/docs/flexible-dimensions-and-quantization).
Those sources establish the model-specific premises; this script establishes
only the stated payload calculation under those premises. A particular API
response, codec, database representation or workload needs its own verification.
