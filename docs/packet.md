# Schema

```

```

| Abstract            | Extensible | Status       | Identifiable | Custom Properties | Additional Properties | Defined In |
| ------------------- | ---------- | ------------ | ------------ | ----------------- | --------------------- | ---------- |
| Can be instantiated | No         | Experimental | No           | Forbidden         | Forbidden             |            |

# Properties

| Property                    | Type       | Required     | Nullable | Defined by    |
| --------------------------- | ---------- | ------------ | -------- | ------------- |
| [authors](#authors)         | `object[]` | **Required** | No       | (this schema) |
| [collections](#collections) | `object[]` | **Required** | No       | (this schema) |
| [metadata](#metadata)       | `object`   | Optional     | No       | (this schema) |
| [organisms](#organisms)     | `object[]` | Optional     | No       | (this schema) |
| [parts](#parts)             | `object[]` | **Required** | No       | (this schema) |
| [plates](#plates)           | `object[]` | Optional     | No       | (this schema) |
| [samples](#samples)         | `object[]` | Optional     | No       | (this schema) |
| [wells](#wells)             | `object[]` | Optional     | No       | (this schema) |

## authors

`authors`

- is **required**
- type: `object[]`
- defined in this schema

### authors Type

Array type: `object[]`

All items must be of the type: `object` with following properties:

| Property      | Type   | Required     |
| ------------- | ------ | ------------ |
| `affiliation` | string | Optional     |
| `email`       | string | **Required** |
| `name`        | string | **Required** |
| `orcid`       | string | Optional     |
| `tags`        | array  | Optional     |
| `uuid`        | string | **Required** |

#### affiliation

`affiliation`

- is optional
- type: `string`

##### affiliation Type

`string`

#### email

`email`

- is **required**
- type: `string`

##### email Type

`string`

- format: `email` – email address (according to [RFC 5322, section 3.4.1](https://tools.ietf.org/html/rfc5322))

#### name

`name`

- is **required**
- type: `string`

##### name Type

`string`

#### orcid

`orcid`

- is optional
- type: `string`

##### orcid Type

`string`

#### tags

`tags`

- is optional
- type: `string[]`

##### tags Type

Array type: `string[]`

All items must be of the type: `string`

#### uuid

`uuid`

- is **required**
- type: `string`

##### uuid Type

`string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5B0-9a-f%5D%7B8%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B12%7D%24)):

```regex
^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$
```

## collections

`collections`

- is **required**
- type: `object[]`
- defined in this schema

### collections Type

Array type: `object[]`

All items must be of the type: `object` with following properties:

| Property      | Type   | Required     |
| ------------- | ------ | ------------ |
| `name`        | string | **Required** |
| `parent_uuid` | string | Optional     |
| `readme`      | string | **Required** |
| `uuid`        | string | **Required** |

#### name

`name`

- is **required**
- type: `string`

##### name Type

`string`

#### parent_uuid

`parent_uuid`

- is optional
- type: `string`

##### parent_uuid Type

`string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5B0-9a-f%5D%7B8%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B12%7D%24)):

```regex
^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$
```

#### readme

`readme`

- is **required**
- type: `string`

##### readme Type

`string`

#### uuid

`uuid`

- is **required**
- type: `string`

##### uuid Type

`string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5B0-9a-f%5D%7B8%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B12%7D%24)):

```regex
^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$
```

## metadata

`metadata`

- is optional
- type: `object`
- defined in this schema

### metadata Type

`object` with following properties:

| Property | Type | Required |
| -------- | ---- | -------- |


## organisms

`organisms`

- is optional
- type: `object[]`
- defined in this schema

### organisms Type

Array type: `object[]`

All items must be of the type: `object` with following properties:

| Property   | Type   | Required     |
| ---------- | ------ | ------------ |
| `genotype` | string | Optional     |
| `name`     | string | **Required** |
| `tags`     | array  | Optional     |
| `uuid`     | string | **Required** |

#### genotype

`genotype`

- is optional
- type: `string`

##### genotype Type

`string`

#### name

`name`

- is **required**
- type: `string`

##### name Type

`string`

#### tags

`tags`

- is optional
- type: `string[]`

##### tags Type

Array type: `string[]`

All items must be of the type: `string`

#### uuid

`uuid`

- is **required**
- type: `string`

##### uuid Type

`string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5B0-9a-f%5D%7B8%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B12%7D%24)):

```regex
^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$
```

## parts

`parts`

- is **required**
- type: `object[]`
- defined in this schema

### parts Type

Array type: `object[]`

All items must be of the type: `object` with following properties:

| Property               | Type   | Required     |
| ---------------------- | ------ | ------------ |
| `authour_uuid`         | string | Optional     |
| `barcode`              | string | Optional     |
| `collection_id`        | string | **Required** |
| `description`          | string | **Required** |
| `full_sequence`        | string | **Required** |
| `genbank`              | object | Optional     |
| `gene_id`              | string | Optional     |
| `name`                 | string | **Required** |
| `optimized_sequence`   | string | Optional     |
| `original_sequence`    | string | Optional     |
| `part_type`            | string | Optional     |
| `primer_for`           | string | Optional     |
| `primer_rev`           | string | Optional     |
| `synthesized_sequence` | string | Optional     |
| `tags`                 | array  | Optional     |
| `translation`          | string | Optional     |
| `uuid`                 | string | **Required** |
| `vector`               | string | Optional     |

#### authour_uuid

`authour_uuid`

- is optional
- type: `string`

##### authour_uuid Type

`string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5B0-9a-f%5D%7B8%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B12%7D%24)):

```regex
^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$
```

#### barcode

`barcode`

- is optional
- type: `string`

##### barcode Type

`string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5BATGC%5D*%24)):

```regex
^[ATGC]*$
```

#### collection_id

`collection_id`

- is **required**
- type: `string`

##### collection_id Type

`string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5B0-9a-f%5D%7B8%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B12%7D%24)):

```regex
^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$
```

#### description

`description`

- is **required**
- type: `string`

##### description Type

`string`

#### full_sequence

`full_sequence`

- is **required**
- type: `string`

##### full_sequence Type

`string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5BATGC%5D*%24)):

```regex
^[ATGC]*$
```

#### genbank

`genbank`

- is optional
- type: `object`

##### genbank Type

`object` with following properties:

| Property | Type | Required |
| -------- | ---- | -------- |


#### gene_id

`gene_id`

- is optional
- type: `string`

##### gene_id Type

`string`

#### name

`name`

- is **required**
- type: `string`

##### name Type

`string`

#### optimized_sequence

`optimized_sequence`

- is optional
- type: `string`

##### optimized_sequence Type

`string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5BATGC%5D*%24)):

```regex
^[ATGC]*$
```

#### original_sequence

`original_sequence`

- is optional
- type: `string`

##### original_sequence Type

`string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5BATGC%5D*%24)):

```regex
^[ATGC]*$
```

#### part_type

`part_type`

- is optional
- type: `enum`

The value of this property **must** be equal to one of the [known values below](#parts-known-values).

##### part_type Known Values

| Value         | Description |
| ------------- | ----------- |
| `cds`         |             |
| `promoter`    |             |
| `terminator`  |             |
| `rbs`         |             |
| `plasmid`     |             |
| `partial_seq` |             |
| `linear_dna`  |             |

#### primer_for

`primer_for`

- is optional
- type: `string`

##### primer_for Type

`string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5BATGC%5D*%24)):

```regex
^[ATGC]*$
```

#### primer_rev

`primer_rev`

- is optional
- type: `string`

##### primer_rev Type

`string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5BATGC%5D*%24)):

```regex
^[ATGC]*$
```

#### synthesized_sequence

`synthesized_sequence`

- is optional
- type: `string`

##### synthesized_sequence Type

`string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5BATGC%5D*%24)):

```regex
^[ATGC]*$
```

#### tags

`tags`

- is optional
- type: `string[]`

##### tags Type

Array type: `string[]`

All items must be of the type: `string`

#### translation

`translation`

- is optional
- type: `string`

##### translation Type

`string`

#### uuid

`uuid`

- is **required**
- type: `string`

##### uuid Type

`string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5B0-9a-f%5D%7B8%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B12%7D%24)):

```regex
^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$
```

#### vector

`vector`

- is optional
- type: `string`

##### vector Type

`string`

## plates

`plates`

- is optional
- type: `object[]`
- defined in this schema

### plates Type

Array type: `object[]`

All items must be of the type: `object` with following properties:

| Property          | Type   | Required     |
| ----------------- | ------ | ------------ |
| `breadcrumb`      | string | **Required** |
| `notes`           | string | Optional     |
| `plate_form`      | string | **Required** |
| `plate_name`      | string | **Required** |
| `plate_type`      | string | **Required** |
| `plate_vendor_id` | string | Optional     |
| `protocol_uuid`   | string | Optional     |
| `status`          | string | **Required** |
| `uuid`            | string | **Required** |

#### breadcrumb

`breadcrumb`

- is **required**
- type: `string`

##### breadcrumb Type

`string`

#### notes

`notes`

- is optional
- type: `string`

##### notes Type

`string`

#### plate_form

`plate_form`

- is **required**
- type: `enum`

The value of this property **must** be equal to one of the [known values below](#plates-known-values).

##### plate_form Known Values

| Value         | Description |
| ------------- | ----------- |
| `standard96`  |             |
| `deep96`      |             |
| `standard384` |             |
| `deep384`     |             |

#### plate_name

`plate_name`

- is **required**
- type: `string`

##### plate_name Type

`string`

#### plate_type

`plate_type`

- is **required**
- type: `enum`

The value of this property **must** be equal to one of the [known values below](#plates-known-values).

##### plate_type Known Values

| Value                    | Description |
| ------------------------ | ----------- |
| `archive_glycerol_stock` |             |
| `glycerol_stock`         |             |
| `culture`                |             |
| `distro`                 |             |

#### plate_vendor_id

`plate_vendor_id`

- is optional
- type: `string`

##### plate_vendor_id Type

`string`

#### protocol_uuid

`protocol_uuid`

- is optional
- type: `string`

##### protocol_uuid Type

`string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5B0-9a-f%5D%7B8%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B12%7D%24)):

```regex
^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$
```

#### status

`status`

- is **required**
- type: `enum`

The value of this property **must** be equal to one of the [known values below](#plates-known-values).

##### status Known Values

| Value     | Description |
| --------- | ----------- |
| `Planned` |             |
| `Stocked` |             |
| `Trashed` |             |

#### uuid

`uuid`

- is **required**
- type: `string`

##### uuid Type

`string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5B0-9a-f%5D%7B8%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B12%7D%24)):

```regex
^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$
```

## samples

`samples`

- is optional
- type: `object[]`
- defined in this schema

### samples Type

Array type: `object[]`

All items must be of the type: `object` with following properties:

| Property       | Type   | Required     |
| -------------- | ------ | ------------ |
| `derived_from` | string | Optional     |
| `evidence`     | string | **Required** |
| `part_uuid`    | string | **Required** |
| `status`       | string | **Required** |
| `uuid`         | string | **Required** |
| `vendor`       | string | Optional     |
| `wells`        | array  | Optional     |

#### derived_from

`derived_from`

- is optional
- type: `string`

##### derived_from Type

`string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5B0-9a-f%5D%7B8%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B12%7D%24)):

```regex
^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$
```

#### evidence

`evidence`

- is **required**
- type: `enum`

The value of this property **must** be equal to one of the [known values below](#samples-known-values).

##### evidence Known Values

| Value             | Description |
| ----------------- | ----------- |
| `Twist_Confirmed` |             |
| `NGS`             |             |
| `Sanger`          |             |
| `Nanopore`        |             |
| `Derived`         |             |

#### part_uuid

`part_uuid`

- is **required**
- type: `string`

##### part_uuid Type

`string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5B0-9a-f%5D%7B8%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B12%7D%24)):

```regex
^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$
```

#### status

`status`

- is **required**
- type: `enum`

The value of this property **must** be equal to one of the [known values below](#samples-known-values).

##### status Known Values

| Value       | Description |
| ----------- | ----------- |
| `Confirmed` |             |
| `Mutated`   |             |

#### uuid

`uuid`

- is **required**
- type: `string`

##### uuid Type

`string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5B0-9a-f%5D%7B8%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B12%7D%24)):

```regex
^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$
```

#### vendor

`vendor`

- is optional
- type: `string`

##### vendor Type

`string`

#### wells

`wells`

- is optional
- type: `string[]`

##### wells Type

Array type: `string[]`

All items must be of the type: `string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5B0-9a-f%5D%7B8%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B12%7D%24)):

```regex
^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$
```

## wells

`wells`

- is optional
- type: `object[]`
- defined in this schema

### wells Type

Array type: `object[]`

All items must be of the type: `object` with following properties:

| Property        | Type   | Required     |
| --------------- | ------ | ------------ |
| `address`       | string | **Required** |
| `media`         | string | **Required** |
| `organism`      | string | Optional     |
| `organism_uuid` | string | Optional     |
| `plate_uuid`    | string | **Required** |
| `quantity`      |        | Optional     |
| `samples`       | array  | **Required** |
| `uuid`          | string | **Required** |
| `volume`        | number | **Required** |

#### address

`address`

- is **required**
- type: `enum`

The value of this property **must** be equal to one of the [known values below](#wells-known-values).

##### address Known Values

| Value | Description |
| ----- | ----------- |
| `A1`  |             |
| `A2`  |             |
| `A3`  |             |
| `A4`  |             |
| `A5`  |             |
| `A6`  |             |
| `A7`  |             |
| `A8`  |             |
| `A9`  |             |
| `A10` |             |
| `A11` |             |
| `A12` |             |
| `A13` |             |
| `A14` |             |
| `A15` |             |
| `A16` |             |
| `A17` |             |
| `A18` |             |
| `A19` |             |
| `A20` |             |
| `A21` |             |
| `A22` |             |
| `A23` |             |
| `A24` |             |
| `B1`  |             |
| `B2`  |             |
| `B3`  |             |
| `B4`  |             |
| `B5`  |             |
| `B6`  |             |
| `B7`  |             |
| `B8`  |             |
| `B9`  |             |
| `B10` |             |
| `B11` |             |
| `B12` |             |
| `B13` |             |
| `B14` |             |
| `B15` |             |
| `B16` |             |
| `B17` |             |
| `B18` |             |
| `B19` |             |
| `B20` |             |
| `B21` |             |
| `B22` |             |
| `B23` |             |
| `B24` |             |
| `C1`  |             |
| `C2`  |             |
| `C3`  |             |
| `C4`  |             |
| `C5`  |             |
| `C6`  |             |
| `C7`  |             |
| `C8`  |             |
| `C9`  |             |
| `C10` |             |
| `C11` |             |
| `C12` |             |
| `C13` |             |
| `C14` |             |
| `C15` |             |
| `C16` |             |
| `C17` |             |
| `C18` |             |
| `C19` |             |
| `C20` |             |
| `C21` |             |
| `C22` |             |
| `C23` |             |
| `C24` |             |
| `D1`  |             |
| `D2`  |             |
| `D3`  |             |
| `D4`  |             |
| `D5`  |             |
| `D6`  |             |
| `D7`  |             |
| `D8`  |             |
| `D9`  |             |
| `D10` |             |
| `D11` |             |
| `D12` |             |
| `D13` |             |
| `D14` |             |
| `D15` |             |
| `D16` |             |
| `D17` |             |
| `D18` |             |
| `D19` |             |
| `D20` |             |
| `D21` |             |
| `D22` |             |
| `D23` |             |
| `D24` |             |
| `E1`  |             |
| `E2`  |             |
| `E3`  |             |
| `E4`  |             |
| `E5`  |             |
| `E6`  |             |
| `E7`  |             |
| `E8`  |             |
| `E9`  |             |
| `E10` |             |
| `E11` |             |
| `E12` |             |
| `E13` |             |
| `E14` |             |
| `E15` |             |
| `E16` |             |
| `E17` |             |
| `E18` |             |
| `E19` |             |
| `E20` |             |
| `E21` |             |
| `E22` |             |
| `E23` |             |
| `E24` |             |
| `F1`  |             |
| `F2`  |             |
| `F3`  |             |
| `F4`  |             |
| `F5`  |             |
| `F6`  |             |
| `F7`  |             |
| `F8`  |             |
| `F9`  |             |
| `F10` |             |
| `F11` |             |
| `F12` |             |
| `F13` |             |
| `F14` |             |
| `F15` |             |
| `F16` |             |
| `F17` |             |
| `F18` |             |
| `F19` |             |
| `F20` |             |
| `F21` |             |
| `F22` |             |
| `F23` |             |
| `F24` |             |
| `G1`  |             |
| `G2`  |             |
| `G3`  |             |
| `G4`  |             |
| `G5`  |             |
| `G6`  |             |
| `G7`  |             |
| `G8`  |             |
| `G9`  |             |
| `G10` |             |
| `G11` |             |
| `G12` |             |
| `G13` |             |
| `G14` |             |
| `G15` |             |
| `G16` |             |
| `G17` |             |
| `G18` |             |
| `G19` |             |
| `G20` |             |
| `G21` |             |
| `G22` |             |
| `G23` |             |
| `G24` |             |
| `H1`  |             |
| `H2`  |             |
| `H3`  |             |
| `H4`  |             |
| `H5`  |             |
| `H6`  |             |
| `H7`  |             |
| `H8`  |             |
| `H9`  |             |
| `H10` |             |
| `H11` |             |
| `H12` |             |
| `H13` |             |
| `H14` |             |
| `H15` |             |
| `H16` |             |
| `H17` |             |
| `H18` |             |
| `H19` |             |
| `H20` |             |
| `H21` |             |
| `H22` |             |
| `H23` |             |
| `H24` |             |
| `I1`  |             |
| `I2`  |             |
| `I3`  |             |
| `I4`  |             |
| `I5`  |             |
| `I6`  |             |
| `I7`  |             |
| `I8`  |             |
| `I9`  |             |
| `I10` |             |
| `I11` |             |
| `I12` |             |
| `I13` |             |
| `I14` |             |
| `I15` |             |
| `I16` |             |
| `I17` |             |
| `I18` |             |
| `I19` |             |
| `I20` |             |
| `I21` |             |
| `I22` |             |
| `I23` |             |
| `I24` |             |
| `J1`  |             |
| `J2`  |             |
| `J3`  |             |
| `J4`  |             |
| `J5`  |             |
| `J6`  |             |
| `J7`  |             |
| `J8`  |             |
| `J9`  |             |
| `J10` |             |
| `J11` |             |
| `J12` |             |
| `J13` |             |
| `J14` |             |
| `J15` |             |
| `J16` |             |
| `J17` |             |
| `J18` |             |
| `J19` |             |
| `J20` |             |
| `J21` |             |
| `J22` |             |
| `J23` |             |
| `J24` |             |
| `K1`  |             |
| `K2`  |             |
| `K3`  |             |
| `K4`  |             |
| `K5`  |             |
| `K6`  |             |
| `K7`  |             |
| `K8`  |             |
| `K9`  |             |
| `K10` |             |
| `K11` |             |
| `K12` |             |
| `K13` |             |
| `K14` |             |
| `K15` |             |
| `K16` |             |
| `K17` |             |
| `K18` |             |
| `K19` |             |
| `K20` |             |
| `K21` |             |
| `K22` |             |
| `K23` |             |
| `K24` |             |
| `L1`  |             |
| `L2`  |             |
| `L3`  |             |
| `L4`  |             |
| `L5`  |             |
| `L6`  |             |
| `L7`  |             |
| `L8`  |             |
| `L9`  |             |
| `L10` |             |
| `L11` |             |
| `L12` |             |
| `L13` |             |
| `L14` |             |
| `L15` |             |
| `L16` |             |
| `L17` |             |
| `L18` |             |
| `L19` |             |
| `L20` |             |
| `L21` |             |
| `L22` |             |
| `L23` |             |
| `L24` |             |
| `M1`  |             |
| `M2`  |             |
| `M3`  |             |
| `M4`  |             |
| `M5`  |             |
| `M6`  |             |
| `M7`  |             |
| `M8`  |             |
| `M9`  |             |
| `M10` |             |
| `M11` |             |
| `M12` |             |
| `M13` |             |
| `M14` |             |
| `M15` |             |
| `M16` |             |
| `M17` |             |
| `M18` |             |
| `M19` |             |
| `M20` |             |
| `M21` |             |
| `M22` |             |
| `M23` |             |
| `M24` |             |
| `N1`  |             |
| `N2`  |             |
| `N3`  |             |
| `N4`  |             |
| `N5`  |             |
| `N6`  |             |
| `N7`  |             |
| `N8`  |             |
| `N9`  |             |
| `N10` |             |
| `N11` |             |
| `N12` |             |
| `N13` |             |
| `N14` |             |
| `N15` |             |
| `N16` |             |
| `N17` |             |
| `N18` |             |
| `N19` |             |
| `N20` |             |
| `N21` |             |
| `N22` |             |
| `N23` |             |
| `N24` |             |
| `O1`  |             |
| `O2`  |             |
| `O3`  |             |
| `O4`  |             |
| `O5`  |             |
| `O6`  |             |
| `O7`  |             |
| `O8`  |             |
| `O9`  |             |
| `O10` |             |
| `O11` |             |
| `O12` |             |
| `O13` |             |
| `O14` |             |
| `O15` |             |
| `O16` |             |
| `O17` |             |
| `O18` |             |
| `O19` |             |
| `O20` |             |
| `O21` |             |
| `O22` |             |
| `O23` |             |
| `O24` |             |
| `P1`  |             |
| `P2`  |             |
| `P3`  |             |
| `P4`  |             |
| `P5`  |             |
| `P6`  |             |
| `P7`  |             |
| `P8`  |             |
| `P9`  |             |
| `P10` |             |
| `P11` |             |
| `P12` |             |
| `P13` |             |
| `P14` |             |
| `P15` |             |
| `P16` |             |
| `P17` |             |
| `P18` |             |
| `P19` |             |
| `P20` |             |
| `P21` |             |
| `P22` |             |
| `P23` |             |
| `P24` |             |

#### media

`media`

- is **required**
- type: `string`

##### media Type

`string`

#### organism

`organism`

- is optional
- type: `string`

##### organism Type

`string`

#### organism_uuid

`organism_uuid`

- is optional
- type: `string`

##### organism_uuid Type

`string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5B0-9a-f%5D%7B8%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B12%7D%24)):

```regex
^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$
```

#### plate_uuid

`plate_uuid`

- is **required**
- type: `string`

##### plate_uuid Type

`string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5B0-9a-f%5D%7B8%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B12%7D%24)):

```regex
^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$
```

#### quantity

`quantity`

- is optional
- type: complex

##### quantity Type

**One** of the following _conditions_ need to be fulfilled.

#### Condition 1

`number`

#### Condition 2

#### samples

`samples`

- is **required**
- type: `string[]`

##### samples Type

Array type: `string[]`

All items must be of the type: `string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5B0-9a-f%5D%7B8%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B12%7D%24)):

```regex
^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$
```

#### uuid

`uuid`

- is **required**
- type: `string`

##### uuid Type

`string`

All instances must conform to this regular expression (test examples
[here](https://regexr.com/?expression=%5E%5B0-9a-f%5D%7B8%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B4%7D-%5B0-9a-f%5D%7B12%7D%24)):

```regex
^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$
```

#### volume

`volume`

- is **required**
- type: `number`

##### volume Type

`number`
