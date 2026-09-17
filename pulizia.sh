#!/bin/bash
# GENERATO DA inventario.py — RILEGGERE PRIMA DI ESEGUIRE.
# Non cancella nulla: raccoglie i log in log/, sposta il resto in _archivio/.
set -e
mkdir -p log _archivio/spedizioni _archivio/duplicati

mv -n spatial_ref2.log log/ 2>/dev/null || true
mv -n spatial_ref3.log log/ 2>/dev/null || true
mv -n grafo_corretto.log log/ 2>/dev/null || true
mv -n lgb_ristretto.log log/ 2>/dev/null || true
mv -n sparse_fixed.log log/ 2>/dev/null || true
mv -n randk.log log/ 2>/dev/null || true
mv -n lgbES.log log/ 2>/dev/null || true
mv -n geo_rimedio.log log/ 2>/dev/null || true
mv -n a6_esteso.log log/ 2>/dev/null || true
mv -n KIT_MANIFEST.txt log/ 2>/dev/null || true
mv -n precisione.log log/ 2>/dev/null || true
mv -n capacity_check.log log/ 2>/dev/null || true
mv -n sparse_5semi.log log/ 2>/dev/null || true
mv -n wgate_placebo.log log/ 2>/dev/null || true
mv -n capacity_check16.log log/ 2>/dev/null || true
mv -n shift_check.log log/ 2>/dev/null || true
mv -n findings_rigenerato.log log/ 2>/dev/null || true
mv -n wgate.log log/ 2>/dev/null || true
mv -n lgb_regolarizzato.log log/ 2>/dev/null || true
mv -n KIT_MANIFEST_A.txt log/ 2>/dev/null || true
mv -n onboardB.log log/ 2>/dev/null || true
mv -n profcheck.txt log/ 2>/dev/null || true
mv -n prior_check.log log/ 2>/dev/null || true
mv -n a6_nonlin.log log/ 2>/dev/null || true
mv -n geo_campagna.log log/ 2>/dev/null || true
mv -n metrics_lgbfair.log log/ 2>/dev/null || true
mv -n KIT_MANIFEST_D.txt log/ 2>/dev/null || true
mv -n metrics.log log/ 2>/dev/null || true
mv -n simnode.txt log/ 2>/dev/null || true
mv -n alpha_gbdt.log log/ 2>/dev/null || true
mv -n spatial_ref.log log/ 2>/dev/null || true
mv -n stid.log log/ 2>/dev/null || true
mv -n attach_check.log log/ 2>/dev/null || true
mv -n identita.log log/ 2>/dev/null || true
mv -n a6_proiezione.log log/ 2>/dev/null || true
mv -n meteo_permutato.log log/ 2>/dev/null || true
mv -n grid_E12.log log/ 2>/dev/null || true
mv -n onboard_canonico.log log/ 2>/dev/null || true
mv -n cellaC.log log/ 2>/dev/null || true
mv -n spatial_ref3_varianti.log log/ 2>/dev/null || true
mv -n emb_abl.log log/ 2>/dev/null || true
mv -n subsetcheck.txt log/ 2>/dev/null || true
mv -n leaderboard_rigenerata.log log/ 2>/dev/null || true
mv -n placebo_check.log log/ 2>/dev/null || true
mv -n densrand.log log/ 2>/dev/null || true
mv -n gomo_corretto.log log/ 2>/dev/null || true
mv -n subset_check_citta.log log/ 2>/dev/null || true
mv -n metrics_lgb.log log/ 2>/dev/null || true
mv -n campagna_fascia.log log/ 2>/dev/null || true
mv -n onboard_aggregates.txt log/ 2>/dev/null || true
mv -n campagna_neurale_B.log log/ 2>/dev/null || true
mv -n densefix.log log/ 2>/dev/null || true
mv -n descrittore.log log/ 2>/dev/null || true
mv -n campagna_d15.log log/ 2>/dev/null || true
mv -n emb_abl_3semi.log log/ 2>/dev/null || true
mv -n alpha_neurale.log log/ 2>/dev/null || true
mv -n campagna_neurale.log log/ 2>/dev/null || true
mv -n validazione.log log/ 2>/dev/null || true
mv -n wnotime.log log/ 2>/dev/null || true
mv -n models/onboard_base_permcheck_mad.log log/ 2>/dev/null || true
mv -n models/onboardC.log log/ 2>/dev/null || true
mv -n models/onboardB.log log/ 2>/dev/null || true
mv -n models/onboard_base_permcheck_lon.log log/ 2>/dev/null || true
mv -n models/onboard_rerun.log log/ 2>/dev/null || true
mv -n models/onboard_base_permcheck_mel.log log/ 2>/dev/null || true
mv -n models/precip.log log/ 2>/dev/null || true
mv -n models/sparse_geo.log log/ 2>/dev/null || true
mv -n models/sparse_geoF.log log/ 2>/dev/null || true
mv -n models/winabl.log log/ 2>/dev/null || true
mv -n results/componenti/sparse_geoF.log log/ 2>/dev/null || true
mv -n results/onboarding/onboard_base_permcheck_mad.log log/ 2>/dev/null || true
mv -n results/onboarding/onboardC.log log/ 2>/dev/null || true
mv -n results/onboarding/onboardB.log log/ 2>/dev/null || true
mv -n results/onboarding/onboard_base_permcheck_lon.log log/ 2>/dev/null || true
mv -n results/onboarding/onboard_rerun.log log/ 2>/dev/null || true
mv -n results/onboarding/onboard_base_permcheck_mel.log log/ 2>/dev/null || true

# I log restano LEGGIBILI in log/. Per comprimerli, decommentare:
# tar czf log.tgz log && rm -rf log

mv -n punto_C_placebo_20260727.tgz _archivio/spedizioni/ 2>/dev/null || true
mv -n punto_B_20260727.tgz _archivio/spedizioni/ 2>/dev/null || true
mv -n campagna_5semi_20260804.tgz _archivio/spedizioni/ 2>/dev/null || true
mv -n kit_onboarding_20260727.tgz _archivio/spedizioni/ 2>/dev/null || true
mv -n punto_D_metriche_completo_20260729.tgz _archivio/spedizioni/ 2>/dev/null || true
mv -n kit_MOTION_completo_20260729.tgz _archivio/spedizioni/ 2>/dev/null || true
mv -n obiezione_2_1_griglia_20260731.tgz _archivio/spedizioni/ 2>/dev/null || true
mv -n riferimenti_R3_calibrati_20260730.tgz _archivio/spedizioni/ 2>/dev/null || true
mv -n R3_scomposizione_20260731.tgz _archivio/spedizioni/ 2>/dev/null || true
mv -n kit_collega_20260727_A.tgz _archivio/spedizioni/ 2>/dev/null || true
mv -n punti_3_5_20260730.tgz _archivio/spedizioni/ 2>/dev/null || true
mv -n riferimenti_spaziali_R3_20260730.tgz _archivio/spedizioni/ 2>/dev/null || true
mv -n punto7_completo_20260731.tgz _archivio/spedizioni/ 2>/dev/null || true
mv -n punto_M2_riferimenti_spaziali_20260729.tgz _archivio/spedizioni/ 2>/dev/null || true
mv -n app/Archivio.zip _archivio/spedizioni/ 2>/dev/null || true
mv -n data_collection/traffic4cast/MELBOURNE_2022.zip _archivio/spedizioni/ 2>/dev/null || true
mv -n data_collection/traffic4cast/LONDON_2022.zip _archivio/spedizioni/ 2>/dev/null || true
mv -n data_collection/traffic4cast/MADRID_2022.zip _archivio/spedizioni/ 2>/dev/null || true

mv -n '~$TION_deliverable_previsione_traffico.docx' _archivio/duplicati/ 2>/dev/null || true
mv -n 'app/make_geo_graphs 2.py' _archivio/duplicati/ 2>/dev/null || true
mv -n 'app/genera_varianti_soglia 20.05.59.py' _archivio/duplicati/ 2>/dev/null || true
mv -n 'app/caratterizza_radar 2.py' _archivio/duplicati/ 2>/dev/null || true
mv -n models/sparse_geo_short_s1.csv.INVALID _archivio/duplicati/ 2>/dev/null || true
mv -n models/sparse_geo_long_s2.csv.INVALID _archivio/duplicati/ 2>/dev/null || true
mv -n models/sparse_geo_long_s1.csv.INVALID _archivio/duplicati/ 2>/dev/null || true
mv -n models/sparse_geo_short_s2.csv.INVALID _archivio/duplicati/ 2>/dev/null || true
mv -n models/sparse_geo_short_s0.csv.INVALID _archivio/duplicati/ 2>/dev/null || true
mv -n models/sparse_geo_long_s0.csv.INVALID _archivio/duplicati/ 2>/dev/null || true

echo "fatto. Log in log/, resto in _archivio/. Nulla cancellato."
echo "I CSV NON sono toccati: usare censimento_csv.py."
