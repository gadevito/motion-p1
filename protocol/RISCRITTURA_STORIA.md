# Riscrittura della storia del repository prima della pubblicazione

Data: 2026-10-31. Richiesta del revisore del 31/10/2026. Eseguita su un clone a parte (`~/OR3_pub`), ramo `main` e tag soltanto, con `git filter-repo`; il repo di lavoro non e' stato toccato.

## Motivo e contenuto

1. **Privacy del manoscritto**: la cartella `paper1/` (una copia antica del manoscritto, presente in cinque commit) e' tolta da tutta la storia (`--invert-paths --path paper1/`). Il manoscritto ha il suo repository, non riscritto.
2. **Nomi di ruolo**: nelle versioni passate dei file, il nome di uno strumento di lavoro usato nelle note sulle correzioni e' sostituito dal ruolo («revisione interna», «durante la stesura del manoscritto»), come gia' fatto nelle versioni correnti con la voce 28 del registro; in due messaggi di commit e' tolta una riga di co-autoria che lo citava. Nessun altro contenuto cambia: gli alberi di ogni tag differiscono dai precedenti solo per `paper1/` e per i file con la stringa sostituita (verifica in calce).
3. I tag annotati sono riscritti con gli stessi nomi.

**I file che citano hash di commit (protocolli, congelamenti, registro, manoscritto) non sono stati modificati**: questa tabella e' la chiave di lettura, dal valore citato al commit corrispondente nella storia pubblicata. Registrata come voce 30 del registro delle correzioni.

## Tag

| tag | commit prima | commit pubblicato |
|---|---|---|
| `e15-freeze-20261028` | `f2ce069` | `c503dd8` |
| `paper1-freeze-20261010` | `d80043c` | `d80043c` |
| `paper1-freeze-20261010b` | `416be4e` | `416be4e` |
| `paper1-freeze-20261010c` | `33cafd6` | `33cafd6` |
| `paper1-freeze-20261010d` | `e824dbe` | `e824dbe` |
| `paper1-freeze-20261010e` | `d955198` | `d955198` |
| `paper1-freeze-20261011` | `7652253` | `7652253` |
| `paper1-freeze-20261011b` | `25af2ef` | `25af2ef` |
| `paper1-freeze-20261011c` | `6b32390` | `09edcac` |
| `paper1-freeze-20261012d` | `6c564af` | `bbbf2a7` |
| `paper1-freeze-20261012e` | `0deaf4d` | `3a20a94` |
| `paper1-freeze-20261015f` | `a511b15` | `700a31c` |
| `paper1-freeze-20261015g` | `aff68f0` | `2d20e65` |
| `paper1-freeze-20261015h` | `cdf77c1` | `32daca6` |
| `paper1-freeze-20261028i` | `004e947` | `546e558` |
| `paper1-freeze-20261028j` | `964e4f5` | `923c02e` |
| `paper1-freeze-20261030k` | `6ebac22` | `862434f` |
| `paper1-freeze-20261030l` | `8986779` | `ae4d707` |

## Commit citati (hash prima → hash pubblicato)

| citato | commit prima | commit pubblicato | citato in |
|---|---|---|---|
| `004e947` | `004e94760659` | `546e558` (`546e55808dde`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `03bcece` | `03bcece3ecf2` | `03bcece` (`03bcece3ecf2`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `0656c98` | `0656c98b5862` | `0656c98` (`0656c98b5862`) | `protocol/E5.md` |
| `0d92b4a` | `0d92b4aff1cc` | `02be9e1` (`02be9e174265`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `0deaf4d` | `0deaf4db4c46` | `3a20a94` (`3a20a945b1c1`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `109aca5` | `109aca5b2b29` | `1ce5769` (`1ce57696561d`) | `protocol/REGISTRO_CORREZIONI.md`, `register_of_corrections.en.md` |
| `109db629195b` | `109db629195b` | `02ffebbd510d` (`02ffebbd510d`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `13413a8fa71a` | `13413a8fa71a` | `f90ceafe78b0` (`f90ceafe78b0`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `168d6f5f57d7` | `168d6f5f57d7` | `168d6f5f57d7` (`168d6f5f57d7`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `1b5a4bb` | `1b5a4bb16123` | `fa8ca89` (`fa8ca899a34f`) | `CONGELAMENTO_E15.md` |
| `1f5da08` | `1f5da08476cd` | `1f5da08` (`1f5da08476cd`) | `CONGELAMENTO_E18.md` |
| `1f5da08476cd` | `1f5da08476cd` | `1f5da08476cd` (`1f5da08476cd`) | `CONGELAMENTO_INTEGRAZIONE_FASE3.md` |
| `2363908a38f0` | `2363908a38f0` | `2363908a38f0` (`2363908a38f0`) | `CONGELAMENTO_E3bis.md` |
| `2407be0` | `2407be08e2b1` | `451c499` (`451c4991fc6b`) | `CONGELAMENTO_E18TER.md` |
| `2a39de3` | `2a39de3fcbcf` | `6f67245` (`6f672454afe7`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `305aece` | `305aece6efb4` | `9f63e03` (`9f63e03b429c`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `305aece6efb4` | `305aece6efb4` | `9f63e03b429c` (`9f63e03b429c`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `31944a9` | `31944a9ba765` | `4d0121a` (`4d0121a33549`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `33cafd6e2914` | `33cafd6e2914` | `33cafd6e2914` (`33cafd6e2914`) | `CONGELAMENTO_E3.md` |
| `364bcf88c0ed` | `364bcf88c0ed` | `4608d05390fd` (`4608d05390fd`) | `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `3a4fb99` | `3a4fb9923351` | `2f19a93` (`2f19a934e1ab`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `3f7d8f479e77` | `3f7d8f479e77` | `217624d6f28c` (`217624d6f28c`) | `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `4025ad91c480` | `4025ad91c480` | `46bc854596f9` (`46bc854596f9`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `484a08a6f89b` | `484a08a6f89b` | `d80138accbb7` (`d80138accbb7`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `4bafa5ef0491` | `4bafa5ef0491` | `4bafa5ef0491` (`4bafa5ef0491`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `4bfdb6a` | `4bfdb6a0181c` | `2368641` (`2368641ca40c`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `5af016944005` | `5af016944005` | `5af016944005` (`5af016944005`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `5c27283d466a` | `5c27283d466a` | `e5a84e9565a4` (`e5a84e9565a4`) | `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `5d134f08fc24` | `5d134f08fc24` | `5d134f08fc24` (`5d134f08fc24`) | `CONGELAMENTO_E4.md` |
| `5ddf4770e863` | `5ddf4770e863` | `5ddf4770e863` (`5ddf4770e863`) | `CONGELAMENTO_E7.md` |
| `5f63919` | `5f63919958bb` | `49fe30e` (`49fe30e49693`) | `CONGELAMENTO_E14B.md` |
| `5fe337f0229d` | `5fe337f0229d` | `5fe337f0229d` (`5fe337f0229d`) | `CONGELAMENTO_E5.md` |
| `6112a864f797` | `6112a864f797` | `6112a864f797` (`6112a864f797`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `6629f40` | `6629f40fd549` | `6629f40` (`6629f40fd549`) | `CONGELAMENTO_E6.md`, `protocol/SUMMARIES.en.md` |
| `6629f40fd549` | `6629f40fd549` | `6629f40fd549` (`6629f40fd549`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `680b35ef7a1c` | `680b35ef7a1c` | `680b35ef7a1c` (`680b35ef7a1c`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `6b72236` | `6b722360de76` | `6b72236` (`6b722360de76`) | `CONGELAMENTO_E18.md` |
| `6f0b7bec474b` | `6f0b7bec474b` | `f9fb70b3fe55` (`f9fb70b3fe55`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `7204736f14e8` | `7204736f14e8` | `7204736f14e8` (`7204736f14e8`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `720e3b44fb49` | `720e3b44fb49` | `c878a917cced` (`c878a917cced`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `74000fc` | `74000fcfd3c8` | `de8eec2` (`de8eec266140`) | `CONGELAMENTO_E14B.md`, `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `74c8cbf7d185` | `74c8cbf7d185` | `95f88c742691` (`95f88c742691`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `751980e` | `751980e6a8b2` | `d9f342a` (`d9f342a776cd`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `77f1d902f6c9` | `77f1d902f6c9` | `08775f594325` (`08775f594325`) | `CONGELAMENTO_E14.md` |
| `79e65ef` | `79e65efaa20f` | `aba36bd` (`aba36bd0f4cf`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `820d419c9649` | `820d419c9649` | `820d419c9649` (`820d419c9649`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `821295f19a06` | `821295f19a06` | `821295f19a06` (`821295f19a06`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `82360a6` | `82360a6ead81` | `82360a6` (`82360a6ead81`) | `CONGELAMENTO_E8.md` |
| `83e9a85` | `83e9a858f392` | `83e9a85` (`83e9a858f392`) | `CONGELAMENTO_E18.md`, `protocol/E6bis.md` |
| `853c8474b7ce` | `853c8474b7ce` | `853c8474b7ce` (`853c8474b7ce`) | `CONGELAMENTO_E8.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `8986779e0ed233b885a9db8c222a0a11fa09c296` | `8986779e0ed2` | `ae4d707acf00f28010df0b47929391afcd7a8913` (`ae4d707acf00`) | `protocol/zenodo/ARCHIVI.md` |
| `89a4bba` | `89a4bba8e34b` | `cf33d7c` (`cf33d7cd45a0`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `8bd956d` | `8bd956db4adf` | `16371ed` (`16371edf8986`) | `CONGELAMENTO_E16.md` |
| `8f68ee202c77` | `8f68ee202c77` | `0c093a68d01c` (`0c093a68d01c`) | `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `8f9afbf` | `8f9afbfcdb3a` | `17078fd` (`17078fd8c07a`) | `protocol/REGISTRO_CORREZIONI.md`, `register_of_corrections.en.md` |
| `8f9afbfcdb3a` | `8f9afbfcdb3a` | `17078fd8c07a` (`17078fd8c07a`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `8fbf5fb` | `8fbf5fb63feb` | `093874a` (`093874a25bc7`) | `CONGELAMENTO_E18.md` |
| `964e4f5` | `964e4f5305ba` | `923c02e` (`923c02ee8f2d`) | `CONGELAMENTO_E18.md`, `manoscritto/NOTE_PER_GLI_AUTORI.md`, `protocol/E18.md`, `protocol/REGISTRO_CORREZIONI.md`, `protocol/SUMMARIES.en.md`, `register_of_corrections.en.md` |
| `9a4517c1b9e2` | `9a4517c1b9e2` | `8203e0ae285f` (`8203e0ae285f`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `9bd9908` | `9bd990859b2b` | `086c417` (`086c417d7d34`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `a3400836808b` | `a3400836808b` | `e7a3a53c44cc` (`e7a3a53c44cc`) | `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `a586cedd0281` | `a586cedd0281` | `30e15b872607` (`30e15b872607`) | `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `abca90d` | `abca90d2765f` | `abca90d` (`abca90d2765f`) | `CONGELAMENTO_E8.md` |
| `abf7c1ec70f4` | `abf7c1ec70f4` | `abf7c1ec70f4` (`abf7c1ec70f4`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `acfc69d` | `acfc69dc0067` | `acfc69d` (`acfc69dc0067`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `acfc69dc0067` | `acfc69dc0067` | `acfc69dc0067` (`acfc69dc0067`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `aef38eefb46a` | `aef38eefb46a` | `b0161f5fa2b3` (`b0161f5fa2b3`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `b064cfc5c93b` | `b064cfc5c93b` | `b064cfc5c93b` (`b064cfc5c93b`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `b52522bdd112` | `b52522bdd112` | `01af3f7ac40e` (`01af3f7ac40e`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `b5d08a0` | `b5d08a0ef019` | `8fbeff4` (`8fbeff4dfedf`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `b7878a5` | `b7878a5b31f2` | `5218650` (`52186506d960`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `b7daff826718` | `b7daff826718` | `94d14534758c` (`94d14534758c`) | `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `b7fd4a96a09f` | `b7fd4a96a09f` | `b7fd4a96a09f` (`b7fd4a96a09f`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `baec568` | `baec568611ed` | `0f6343d` (`0f6343d8c366`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `bbabdd6` | `bbabdd6bd4c2` | `0e3d6c0` (`0e3d6c0d6c12`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `bfeea7f06b73` | `bfeea7f06b73` | `569b85bca22e` (`569b85bca22e`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `c15bbb200fab` | `c15bbb200fab` | `5954c9841fa6` (`5954c9841fa6`) | `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `c1e921ea3b21` | `c1e921ea3b21` | `db06fa303df5` (`db06fa303df5`) | `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `c3e6cb303823` | `c3e6cb303823` | `cc286a819da1` (`cc286a819da1`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `c6526af55607` | `c6526af55607` | `c6526af55607` (`c6526af55607`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `c7b42da179e9` | `c7b42da179e9` | `c7b42da179e9` (`c7b42da179e9`) | `CONGELAMENTO_E2.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `c8e60b99eebd` | `c8e60b99eebd` | `2ce7683c6eb8` (`2ce7683c6eb8`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `ce247e0a1fd8` | `ce247e0a1fd8` | `c482c609a875` (`c482c609a875`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `d127a04` | `d127a043e0be` | `e12a2d7` (`e12a2d73b127`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `d127a043e0be` | `d127a043e0be` | `e12a2d73b127` (`e12a2d73b127`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `d80043c971e8` | `d80043c971e8` | `d80043c971e8` (`d80043c971e8`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `d8106f0` | `d8106f07c763` | `d8106f0` (`d8106f07c763`) | `protocol/E8bis.md` |
| `d8e828664d96` | `d8e828664d96` | `d8e828664d96` (`d8e828664d96`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `d8ef81299651` | `d8ef81299651` | `d8ef81299651` (`d8ef81299651`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `dadd2dc2dcb5` | `dadd2dc2dcb5` | `dadd2dc2dcb5` (`dadd2dc2dcb5`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `db9f8f3` | `db9f8f3b1c24` | `db9f8f3` (`db9f8f3b1c24`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `db9f8f3b1c24` | `db9f8f3b1c24` | `db9f8f3b1c24` (`db9f8f3b1c24`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `dc35e91fb1fc` | `dc35e91fb1fc` | `dc35e91fb1fc` (`dc35e91fb1fc`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `e10c579` | `e10c57900ef1` | `f5141bd` (`f5141bd954fb`) | `CONGELAMENTO_E17.md` |
| `e3b05d7` | `e3b05d766a48` | `547a51e` (`547a51ea0148`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `e5ae222` | `e5ae222f525e` | `9f55725` (`9f55725c0cc9`) | `CONGELAMENTO_E18.md`, `manoscritto/figures/tableG_e18.tex`, `protocol/E15.md`, `protocol/E16.md`, `protocol/E17.md` |
| `e824dbee4dc2` | `e824dbee4dc2` | `e824dbee4dc2` (`e824dbee4dc2`) | `CONGELAMENTO_E6.md` |
| `ea02d713e44f` | `ea02d713e44f` | `c58df00f376b` (`c58df00f376b`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `eb7d96a` | `eb7d96a248c0` | `2032a2d` (`2032a2d9cbb3`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `eb7f852afec6` | `eb7f852afec6` | `eb7f852afec6` (`eb7f852afec6`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `f182f7e` | `f182f7e278a7` | `1db30dd` (`1db30dd8bdd1`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `f182f7e278a7` | `f182f7e278a7` | `1db30dd8bdd1` (`1db30dd8bdd1`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `f196e51` | `f196e5154642` | `2bc30bc` (`2bc30bc9bbc8`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `f2ce069` | `f2ce069bdb16` | `c503dd8` (`c503dd8ec354`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `f5d7a8d394dd` | `f5d7a8d394dd` | `f5d7a8d394dd` (`f5d7a8d394dd`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `f79e61e` | `f79e61e6f178` | `ab039e1` (`ab039e1ef35f`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `f79e61e6f178` | `f79e61e6f178` | `ab039e1ef35f` (`ab039e1ef35f`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `f9290bbaa468` | `f9290bbaa468` | `f9290bbaa468` (`f9290bbaa468`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `fb6f7b4` | `fb6f7b47d4b1` | `4ef852b` (`4ef852b4e21e`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `fb6f7b47d4b1` | `fb6f7b47d4b1` | `4ef852b4e21e` (`4ef852b4e21e`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `fc85b2b` | `fc85b2b817b2` | `47040ea` (`47040eac1881`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `fd39b39` | `fd39b395792e` | `418c979` (`418c97971555`) | `manoscritto/NOTE_PER_GLI_AUTORI.md` |
| `fda754ec150f` | `fda754ec150f` | `fda754ec150f` (`fda754ec150f`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |
| `ffac660209ee` | `ffac660209ee` | `ffac660209ee` (`ffac660209ee`) | `protocol/spark/CONFRONTO_paper1-freeze-20261028i.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261028j.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030k.md`, `protocol/spark/CONFRONTO_paper1-freeze-20261030l.md` |

Hash del repository del manoscritto, citati in OR3 e invariati: `0191aab`, `0658afa`, `0d8cb29`, `14d19f7`, `1ea0d70`, `41c960b43984af0b4773e860f2029bae7b408ed1`, `423164c`, `484cc57`, `4c73024`, `5fb9b2d`, `a86604b`, `ae12921`, `ae12921c0671e27c90a4294dcd9905e927bef807`, `bc2a425c597b1006e88e8a5bb002f4100f9b0760`, `c684451`, `cea5e76`, `cea5e7686607a25835d0f845ca49f6ef8e4ac7ea`, `de80ece`, `e48a228`, `ec58eb7`.

## Verifica

Stesso numero di commit su `main` (263) e di tag (18); nessuna occorrenza delle parole sostituite in tutta la storia (contenuti, messaggi, tag, autori); `git log --all -- paper1/` vuoto; alberi dei tag confrontati con quelli di prima (solo `paper1/` rimossa e i file con la stringa sostituita). Strumenti di riscrittura e di verifica tenuti fuori dal repository.
