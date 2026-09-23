# Batch 1: Jev spend log

## Pre-flight smoke test (outside the priced plan below)
Before running the priced batches, 1 request was sent by hand to confirm JevSession, the
question-dict shape, and TYPESAFE_API_KEY all work end to end: model `jev-1.13.0`, 322 input
tokens, 37 output tokens, on a throwaway journalist/professor question dict (not one of the
committed rows; the item text is not part of any fixture). This request counts toward the total
below but not toward any file's row count.
- running total after smoke test: 1

### journalist-professor / gender-pronouns
- rows: 4000 (committed order ['professor', 'journalist'])
- already done (resumed): 0
- to send this run: 4000
- running total before this file: 1
- running total after this file (if sent in full): 4001
- sent 4000 requests, 1,537,513 input tokens, 150,058 output tokens

### architect-interior-designer / gender-pronouns
- rows: 3796 (committed order ['architect', 'interior_designer'])
- already done (resumed): 0
- to send this run: 3796
- running total before this file: 4001
- running total after this file (if sent in full): 7797
- sent 3796 requests, 1,444,676 input tokens, 153,557 output tokens

### dietitian-physician / gender-pronouns
- rows: 4000 (committed order ['physician', 'dietitian'])
- already done (resumed): 0
- to send this run: 4000
- running total before this file: 7797
- running total after this file (if sent in full): 11797
- sent 4000 requests, 1,516,899 input tokens, 144,000 output tokens

### paralegal-attorney / disability
- rows: 2770 (committed order ['attorney', 'paralegal'])
- already done (resumed): 0
- to send this run: 2770
- running total before this file: 11797
- running total after this file (if sent in full): 14567
- sent 2770 requests, 1,069,269 input tokens, 103,660 output tokens

### surgeon-physician / disability
- rows: 2742 (committed order ['surgeon', 'physician'])
- already done (resumed): 0
- to send this run: 2742
- running total before this file: 14567
- running total after this file (if sent in full): 17309
- sent 2742 requests, 1,078,175 input tokens, 102,641 output tokens

### surgeon-physician / ask-twice
- rows: 500 (committed order ['surgeon', 'physician'])
- already done (resumed): 0
- to send this run: 500
- running total before this file: 17309
- running total after this file (if sent in full): 17809
- sent 500 requests, 191,986 input tokens, 18,702 output tokens

### nurse-physician / ask-twice
- rows: 500 (committed order ['physician', 'nurse'])
- already done (resumed): 0
- to send this run: 500
- running total before this file: 17809
- running total after this file (if sent in full): 18309
- sent 500 requests, 190,603 input tokens, 18,000 output tokens

### paralegal-attorney / ask-twice
- rows: 500 (committed order ['attorney', 'paralegal'])
- already done (resumed): 0
- to send this run: 500
- running total before this file: 18309
- running total after this file (if sent in full): 18809
- sent 500 requests, 191,467 input tokens, 18,707 output tokens

### teacher-professor / ask-twice
- rows: 500 (committed order ['professor', 'teacher'])
- already done (resumed): 0
- to send this run: 500
- running total before this file: 18809
- running total after this file (if sent in full): 19309
- sent 500 requests, 193,006 input tokens, 17,984 output tokens

### surgeon-physician / option-order-reversed
- rows: 500 (reversed order ['physician', 'surgeon'] (committed was ['surgeon', 'physician']))
- already done (resumed): 0
- to send this run: 500
- running total before this file: 19309
- running total after this file (if sent in full): 19809
- sent 500 requests, 191,986 input tokens, 18,702 output tokens

### nurse-physician / option-order-reversed
- rows: 500 (reversed order ['nurse', 'physician'] (committed was ['physician', 'nurse']))
- already done (resumed): 0
- to send this run: 500
- running total before this file: 19809
- running total after this file (if sent in full): 20309
- sent 500 requests, 190,603 input tokens, 18,000 output tokens

### paralegal-attorney / option-order-reversed
- rows: 500 (reversed order ['paralegal', 'attorney'] (committed was ['attorney', 'paralegal']))
- already done (resumed): 0
- to send this run: 500
- running total before this file: 20309
- running total after this file (if sent in full): 20809
- sent 500 requests, 191,467 input tokens, 18,711 output tokens

### teacher-professor / option-order-reversed
- rows: 500 (reversed order ['teacher', 'professor'] (committed was ['professor', 'teacher']))
- already done (resumed): 0
- to send this run: 500
- running total before this file: 20809
- running total after this file (if sent in full): 21309
- sent 500 requests, 193,006 input tokens, 17,966 output tokens

## Run summary
- total requests sent this run: 21309
- total requests actually sent (API calls) this run: 21308
- total input tokens this run: 8,180,656
- total output tokens this run: 800,688
