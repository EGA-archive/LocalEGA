# Messages Format

## File in inbox (FEGA → CEGA)
Routing key: **files.inbox**

### Description
Message sent when a new file has been uploaded in the inbox of the user. The message is received by the Submitter Portal and displayed there, so the user can use it to create the metadata.

### Format
Required:
- operation: "upload"
- user: string 
- filepath: string
- filesize: integer
- file_last_modified: timestamp
- encrypted_checksums: array of checksums with this format:
	- type: string
	- value: string

### Example
```json
{
   "user":"oscar",
   "filepath":"31/upload-test-5bfac753c0.txt.c4gh",
   "operation":"upload",
   "encrypted_checksums":[
      {
         "type":"sha256",
         "value":"c3629dd4d17c8eba1067fccdf6cb56a521feb098658076c9b2e73ea445b109b0"
      }
   ],
   "filesize":280,
   "file_last_modified":1697708122
}
```

## File ingestion (CEGA → FEGA)

Routing key: **ingest**

### Description
Message sent when a file has been lined in a run or an analysis in the Submitter Portal, and the ingestion of this file can begin.

### Format
Required:
-   type: “ingest”    
-   user: string    
-   filepath: string    
-   encrypted_checksums: array of checksums with this format:  
	-   type: string    
	-   value: string

### Example
```json
{
   "type":"ingest",
   "user":"oscar",
   "filepath":"32/upload-test-2ae1576919.txt.c4gh",
   "encrypted_checksums":[
      {
         "type":"sha256",
         "value":"248f1a881590e169e72010a946eed93fff7608f2f0002f7eafb48511e00292a5"
      }
   ]
}
```

## File verified (FEGA → CEGA)

Routing key: **files.verified**

### Description
Message sent when the node has correctly verified the file and needs an accession in order to continue with the archival.

### Format
Required:
- type: "verified"
- user: string
- filepath: string
- encrypted_checksums: array of checksums with this format:
	- type: string
	- value: string
- decrypted_checksums: array of checksums with this format:
	- type: string
	- value: string




### Example
```json
{
    "type": "ingest",
    "user": "oscar",
    "filepath": "32/upload-test-161b38e98b.txt.c4gh",
    "encrypted_checksums": [
        {
            "type": "sha256",
            "value": "5545d9eceead9b5077aeaf8de12cf5a6b4d1dc0bc952e2eabb99643ff7fa7238"
        }
    ],
    "decrypted_checksums": [
        {
            "type": "sha256",
            "value": "13434a1c3f7f09eca072892daaa190bf98a9a0d234faab4c16c05ab75821fdf0"
        }
    ]
}
```

## File accession (CEGA → FEGA)
Routing key: **accession**

### Description
Message sent when the node requests an accession for a specific file. 

### Format
Required:
- type: "accession"
- user: string
- filepath: string
- accession_id: string as EGAF accession Id
- decrypted_checksums: array of checksums with this format:
	- type: string
	- value: string

### Example
```json
{
   "type":"accession",
   "user":"oscar",
   "filepath":"32/upload-test-161b38e98b.txt.c4gh",
   "accession_id":"EGAF50000105387",
   "decrypted_checksums":[
      {
         "type":"sha256",
         "value":"13434a1c3f7f09eca072892daaa190bf98a9a0d234faab4c16c05ab75821fdf0"
      }
   ]
}
```

## File completed (FEGA → CEGA)
Routing key: **files.completed**

### Description
Message sent when the file has been successfully archived in the vault of the node, including the backup.

### Format

Required:
- type: "accession"
- user: string
- filepath: string
- accession_id: string as EGAF accession Id
- decrypted_checksums: array of checksums with this format:
	- type: string
	- value: string

### Example
```json
{
    "type": "accession",
    "user": "oscar",
    "filepath": "32/upload-test-161b38e98b.txt.c4gh",
    "accession_id": "EGAF50000105387",
    "decrypted_checksums": [
        {
            "type": "sha256",
            "value": "13434a1c3f7f09eca072892daaa190bf98a9a0d234faab4c16c05ab75821fdf0"
        }
    ]
}
```

## File cancel (CEGA → FEGA)
Routing key: **cancel**

### Description
Message sent when a run or analysis is deleted, or edited to change the linked file in the Submitter Portal.
The purpose of this message is to clean up the staging area, in case the file is still there.

### Format
Required:
- type: "cancel"
- user: string
- filepath: string
- encrypted_checksums: array of checksums with this format:
	- type: string
	- value: string

### Example
```json
{
   "type":"cancel",
   "user":"oscar",
   "filepath":"32/upload-test-161b38e98b.txt.c4gh",
   "encrypted_checksums":[
      {
         "type":"sha256",
         "value":"5545d9eceead9b5077aeaf8de12cf5a6b4d1dc0bc952e2eabb99643ff7fa7238"
      }
   ]
}
```

## Dataset mapping (CEGA → FEGA)
Routing key: **dataset.mapping**

### Description
Message sent when a new dataset, or an edition on an already existing one, is accepted by the node HelpDesk.
It includes the list of files linked in this dataset.

### Format
Required:
- type: "mapping"
- dataset_id: string as EGAD accession ID
- accession_ids: array of strings as EGAF accession Id

### Example
```json
{
   "type":"mapping",
   "dataset_id":"EGAD50000000192",
   "accession_ids":[
      "EGAF50000105387",
      "EGAF50000105388",
      "EGAF50000105389",
      "EGAF50000105390"
   ]
}
```

## Dac-dataset mapping (CEGA → FEGA)
Routing key: **dac.dataset**

### Description
Message sent when a new dataset, or an edition on an already existing one, is accepted by the node HelpDesk.
It includes information about the DAC managing this dataset, the users that are members of this DAC, and any other dataset belonging to this node and managed by this DAC.

### Format

Required:
- type: "dac.dataset"
- accession_id: string as EGAC accession ID
- title: string
- description: string
- datasets: array of dataset information with the following format
	- accession_id: string as EGAD accession ID
	- title: string
	- description: string
- users: array of user information with the following format:
	- email: string
	- country: string
	- username: string
	- full_name: string
	- institution: string
	- password_hash: string
	- member_type: string, accepted values: admin|member
	- is_main: boolean

### Example
```json
{
   "type":"dac.dataset",
   "title":"DAC for testing",
   "users":[
      {
         "email":"aina.jene@crg.eu",
         "country":"Spain",
         "is_main":true,
         "username":"aina.jene@crg.eu",
         "full_name":"Aina Jené",
         "institution":"Centre for Genomic Regulation",
         "member_type":"admin",
         "password_hash":"$S$D.Nk1zCiL1FTim.6UcdhKRuf6.EVSVmJtiqT7LolbEiBnfFeOKRQ"
      },
      {
         "email":"jordi.rambla@crg.eu",
         "country":"Spain",
         "is_main":false,
         "username":"jordi.rambla@crg.eu",
         "full_name":"Jordi Rambla",
         "institution":"Centre for Genomic Regulation",
         "member_type":"member",
         "password_hash":"$S$DlbDwcv/vJFf1eh03AxlCqAHCT0UgK7uiq8JyOqyIgkWKG4QEOEk"
      },
      {
         "email":"sabela.delatorre@crg.eu",
         "country":"Spain",
         "is_main":false,
         "username":"sabela",
         "full_name":"Sabela de la Torre",
         "institution":"Centre for Genomic Regulation",
         "member_type":"admin",
         "password_hash":"$2b$12$9fCXDqZPwJkmw8KfqRWnXeciYiqMer.mPSniH0XPQ01X/XdOcVR.m"
      }
   ],
   "datasets":[
      {
         "title":"Dataset that contains analyses of submission 32",
         "description":"Description of analyses dataset of submission 32",
         "accession_id":"EGAD50000000193"
      },
      {
         "title":"Dataset that contains runs of submission 32",
         "description":"Description of runs dataset of submission 32",
         "accession_id":"EGAD50000000192"
      }
   ],
   "description":"DAC only used for testing all functionalities",
   "accession_id":"EGAC50000000002"
}
```

## DAC information (CEGA → FEGA)
Routing key: **dac**

### Description
Message sent when the DAC title and/or description have been modified. 
The DAC must manage a dataset in this node in order to trigger this message.

### Format
Required:
- type: "dac"
- accession_id: string as EGAC accession ID
- title: string
- description: string

### Example
```json
{
   "type":"dac",
   "title":"DAC only used for testing all functionalities",
   "description":"DAC only used for testing all functionalities",
   "accession_id":"EGAC50000000002"
}
```

## DAC members (CEGA → FEGA)
Routing key: **dac.members**

### Description
Message sent when the members within the DAC have been modified (e.g. a member was removed).
The DAC must manage a dataset in this node in order to trigger this message.

### Format
Required:
- type: "dac.members"
- accession_id: string as EGAC accession ID
- title: string
- description: string
- users: array of user information with the following format:
	- email: string
	- country: string
	- username: string
	- full_name: string
	- institution: string
	- password_hash: string
	- member_type: string, valid values: admin|member
	- is_main: boolean, true if this user is the contact of this DAC

### Example
```json
{
   "type":"dac.members",
   "users":[
      {
         "email":"aina.jene@crg.eu",
         "country":"Spain",
         "is_main":true,
         "username":"aina.jene@crg.eu",
         "full_name":"Aina Jené",
         "institution":"Centre for Genomic Regulation",
         "member_type":"admin",
         "password_hash":"$S$D.Nk1zCiL1FTim.6UcdhKRuf6.EVSVmJtiqT7LolbEiBnfFeOKRQ"
      },
      {
         "email":"sabela.delatorre@crg.eu",
         "country":"Spain",
         "is_main":false,
         "username":"sabela",
         "full_name":"Sabela de la Torre",
         "institution":"Centre for Genomic Regulation",
         "member_type":"admin",
         "password_hash":"$2b$12$9fCXDqZPwJkmw8KfqRWnXeciYiqMer.mPSniH0XPQ01X/XdOcVR.m"
      }
   ],
   "accession_id":"EGAC50000000002"
}
```

## Password updated (CEGA → FEGA)

Routing key: **user.password.updated**

### Description
Message sent when a user related to this node has changed their password in the EGA website.
A user is related to a node when:
- s/he is a member of a DAC managing datasets in this node
or/and
- s/he has been granted access to at least one dataset in this node

### Format
Required:
- type: "password.updated"
- user: string
- password_hash: string, blowfish only

### Example
```json
{
   "type":"password.updated",
   "user":"sabela",
   "password_hash":"$2b$12$IqmF1hxte.zaaPnSliC0duFgFS0U.K2vb/cm6VlbpDa34kvpd9UzS"
}
```

## Contact details updated (CEGA → FEGA)
Routing key: **user.contact.updated**

### Description
Message sent when a user related to this node has updated their information in the EGA website.
A user is related to a node when:
- s/he is a member of a DAC managing datasets in this node
or/and
- s/he has been granted access to at least one dataset in this node

### Format
Required:
- type: "contact.updated"
- user: string
- email: string
- country: string
- full_name: string
- institution: string

### Example
```json
{
   "type":"contact.updated",
   "user":"sabela",
   "email":"Sabela de la Torre",
   "country":"Spain",
   "full_name":"sabela.delatorre@crg.eu",
   "institution":"Barcelona Supercomputing Center"
}
```

## User keys updated (CEGA → FEGA)
Routing key: **user.keys.updated**

### Description
Message sent when a user related to this node has updated their SSH keys in the EGA website.
A user is related to a node when:
- s/he is a member of a DAC managing datasets in this node
or/and
- s/he has been granted access to at least one dataset in this node

### Format
Required:
- type: "keys.updated"
- user: string
- keys: array of SSH keys with the following format:
	- key: string
	- type: string

### Example
```json
{
   "keys":[
      {
         "key":"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJC8WIY+VztGShuajXQS5/Wo7TtyFeJ1MuZeAcDY0tiY sabela@crg",
         "type":"ssh-ed25519"
      },
      {
         "key":"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICulsKa6+cTg5YZVK4EhYJ+0DGUpECscEw2quAhzU2Jy sabela-inbox",
         "type":"ssh-ed25519"
      }
   ],
   "type":"keys.updated",
   "user":"sabela"
}
```

## Permission granted (CEGA → FEGA)
Routing key: **dataset.permission**

### Description
Message sent when a request from a user to access a dataset in this node has been granted in the DAC Portal. It includes information about this user: contact details, password and keys.

### Format
Required:
- type: "permission"
- dataset_id: string as EGAD accession ID
- created_at: date time with format `yyyy-MM-ddTHH:mm:ss.ssssss±hh:mm`
- edited_at: date time with format `yyyy-MM-ddTHH:mm:ss.ssssss±hh:mm`
- users: array of user information with the following format:
	- email: string
	- country: string
	- username: string
	- full_name: string
	- institution: string
	- password_hash: string, blowfish only
- keys: array of SSH keys with the following format:
	- key: string
	- type: string

Optional:
- expires_at: date, when not null, permission will be automatically revoked on this date

### Example
```json
{
   "type":"permission",
   "user":{
      "keys":[
         {
            "key":"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIJC8WIY+VztGShuajXQS5/Wo7TtyFeJ1MuZeAcDY0tiY sabela@crg",
            "type":"ssh-ed25519"
         },
         {
            "key":"ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICulsKa6+cTg5YZVK4EhYJ+0DGUpECscEw2quAhzU2Jy sabela-inbox",
            "type":"ssh-ed25519"
         }
      ],
      "email":"sabela.delatorre@crg.eu",
      "country":"Spain",
      "username":"sabela",
      "full_name":"Sabela de la Torre",
      "institution":"Barcelona Supercomputing Center",
      "password_hash":"$2b$12$IqmF1hxte.zaaPnSliC0duFgFS0U.K2vb/cm6VlbpDa34kvpd9UzS"
   },
   "edited_at":"2023-10-20T10:57:56.981814+00:00",
   "created_at":"2023-10-20T10:57:56.981814+00:00",
   "dataset_id":"EGAD50000000079",
   "expires_at":"None"
}
```

## Permission removed (CEGA → FEGA)
Routing key: **dataset.permission.deleted**

### Description
Message sent when the permission to access a dataset in this node has been removed to a user.

### Format
Required:
- type: "permission.deleted"
- user: string
- dataset_id: string as EGAD accession ID

### Example
```json
{
   "type":"permission.deleted",
   "user":"sabela",
   "dataset_id":"EGAD50000000082"
}
```

## Dataset released (CEGA → FEGA)
Routing key: **dataset.release**

### Description
Message sent when the dataset is released in the node’s HelpDesk Portal. 
This means the dataset is now findable in the EGA website, and users can start requesting access.

### Format
Required:
- type: "release"
- dataset_id: string as EGAD accession ID

### Example
```json
{
   "type":"release",
   "dataset_id":"EGAD50000000192"
}
```
