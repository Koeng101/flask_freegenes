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
At the core of the bionet packet is the `part`. A `part` is a 
