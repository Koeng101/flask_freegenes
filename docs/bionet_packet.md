# Bionet packet

A bionet packet is a collection of information that encompasses most necessary documentation in transferring phsyical biological materials (in particular, plasmid DNA) between two parties.

Before delving into specifics, the general map of a Bionet Packet is the following
```
 _____________       _______       _________       _______       ________
|             | <---|       | <---|         | <---|       |---> |        |
| Collections | <---| Parts | <---| Samples | <---| Wells |---> | Plates |
|_____________| <---|_______| <---|_________| <---|_______|---> |________|
```
- A collection contains many parts
- A part may exist as multiple samples
- A sample may exist in multiple wells
- A plate contains many wells

## The Part
At the core of the bionet packet is the `part`. A `part` contains most information relevant to working with the genetic element it represents.

Fields:

| Field | Parameter | Required? | Enum |
| ----- | --------- | --------- | ---- |
| uuid | A unique identifier | Required ||
| author_uuid | The author's uuid | Required ||
| collection_id | The collection's uuid that this part belongs to | Required ||
| description | A descritpion of this genetic element | Required ||
| name | The genetic element's name | Required ||
| optimized_sequence | The genetic element's sequence | Required ||
| part_type | The type of genetic element | Required | cds, promoter, terminator, rbs, plasmid, partial_seq, linear_dna, vector |
| barcode | A part's unique barcode | Optional ||
| full_sequence | The full sequence of this genetic element INCLUDING vector if possible | Optional ||
| genbank | A JSON representation of the element's would-be genbank file | Optional ||
| original_sequence | The genetic element's original sequence (for historical purposes) | Optional ||
| primer_for | The forward primer to amplify this element | Optional ||
| primer_rev | The reverse primer to amplify this element | Optional ||
| synthesized_sequence | The actual sequence sent to be synthesized by vendor | Optional ||
| tags | A list of tags associated with this element | Optional ||
| translation | The protein translation if this element is a CDS | Optional ||
| vector | The name of the vector this part exists in | Optional ||


