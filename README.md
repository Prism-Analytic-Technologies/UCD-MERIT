# UCD-MERIT

The purpose of this workspace is two-fold: (1) To systematically document existing deficiencies in clinical trial regulation, which we hypothesize, is permitting too many trials with low social or scientific value to move forward; (2) To demonstrate a software instrument that can help to identify (and prevent) such low-value trials by systematically surfacing information about any given trial's epistemic context.

## Data Transformation

- Data is pulled from the source ([Prism's CtGov REST API](https://api.prism.bio/))
- The source API is queried with these parameters:
  - `query=indications.canonical.name:*${indication}`
  - `startDate:<${date}` (the start date of the relevant pivotal trial) 
  - `studyType:INTERVENTIONAL`
  - `interventions.type:DRUG;purpose:TREATMENT`
- Data is transformed according to the [this transformation script](transformation.py) and persisted in a cache.

### Transformation Detail

(TODO: Spencer)

### CtGov API

This API consists of a normalized and enriched copy of clinicaltrials.gov.

#### General Process*

(will be true by the time of publication - there is currently some manual process involved)

On a nightly basis, all clinicaltrial.gov records are pulled and transformed with heavily unit-tested python code. Enrichment sources are pulled anywhere from weekly (MeSH and NCI) to monthly (NCATS). Automated verification tests are run post-upload.

#### Enrichment

##### Sources
- [MeSH](https://www.nlm.nih.gov/mesh/meshhome.html) - for canonical indication mapping
- [NCI (National Cancer Institute) Thesaurus](https://evs.nci.nih.gov/ftp1/NCI_Thesaurus/Thesaurus.FLAT.zip) - for canonical indication and intervention mapping
- [NCATS (National Center for Advancing Translational Sciences)](https://drugs.ncats.io/substances) - for richer and more extensive data about interventions and their regulatory approval status.

##### General Approach

We search for canonical entity in the applicable clinicaltrials.gov fields and choose the best-fit based on simple criteria with this process:
- take all results from a word-bounded contains match between a ctgov field and an entity's canonical name or synonym
- select the most specific match based on
  - an exclusion list (elimiating highly non-specific matches on NCI entities like 'Disease or Disorder')
  - a de-prioritization list (for better-than-nothing but still non-specific entries like 'Digestive System Disorder')
  - term length (i.e. longer terms are generally considered more specfic)

Prior to matching, certain invalid synonyms are suppressed, e.g. from NCI
- 'breast cancer' is listed as a synonym for 'childhood breast carcinoma'
- 'acute' is listed as a synonum for 'acute host versus graft disease'
- 'II' is listed as a synonym for 'ISS Stage II Plasma Cell Myeloma'

##### Entity-Specific Approach
- Indications are mapped from the following trial record elements
  - `FullStudy->Study->ProtocolSection->ConditionsModule->ConditionList`
  - `FullStudy->Study->ProtocolSection->ConditionsModule->Keyword List`
  - `FullStudy->Study->ProtocolSection->IdentificationModule->OfficialTitle`
- Interventions are mapped from the following trial record elements
  - `FullStudy->Study->ProtocolSection->ArmsInterventionsModule->InterventionList->Intervention`


