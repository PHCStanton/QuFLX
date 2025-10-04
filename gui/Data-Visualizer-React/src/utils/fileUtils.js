export const fetchCurrencyPairs = async () => {
  // Static list of currency pairs based on available files
  const availableFiles = [
    'AUDCADOTC_2024_2_2_18.csv',
    'AUDCADOTC_2024_2_5_11.csv',
    'AUDCADOTC_2024_2_6_19.csv',
    'AUDCAD_2024_2_5_11.csv',
    'AUDCAD_2024_2_5_13.csv',
    'AUDCAD_2024_2_5_15.csv',
    'AUDCAD_2024_2_5_21.csv',
    'AUDCHFOTC_2024_2_2_18.csv',
    'AUDCHFOTC_2024_2_5_12.csv',
    'AUDCHFOTC_2024_2_6_19.csv',
    'AUDCHF_2024_2_5_13.csv',
    'AUDJPY_2024_2_6_19.csv',
    'AUDNZDOTC_2024_2_6_16.csv',
    'AUDNZDOTC_2024_2_6_19.csv',
    'AUDUSDOTC_2024_2_5_12.csv',
    'AUDUSDOTC_2024_2_6_16.csv',
    'AUDUSDOTC_2024_2_6_19.csv',
    'CADCHFOTC_2024_2_6_19.csv',
    'CADJPYOTC_2024_2_6_19.csv',
    'CADJPY_2024_2_6_19.csv',
    'CHFJPYOTC_2024_2_5_12.csv',
    'CHFJPYOTC_2024_2_6_16.csv',
    'CHFJPYOTC_2024_2_6_19.csv',
    'EURCAD_2024_2_5_11.csv',
    'EURCAD_2024_2_6_19.csv',
    'EURCHFOTC_2024_2_6_19.csv',
    'EURGBPOTC_2024_2_5_12.csv',
    'EURGBPOTC_2024_2_6_19.csv',
    'EURJPYOTC_2024_2_5_12.csv',
    'EURJPY_2024_2_5_11.csv',
    'EURNZDOTC_2024_2_5_12.csv',
    'EURRUBOTC_2024_2_5_12.csv',
    'EURRUBOTC_2024_2_6_19.csv',
    'EURUSDOTC_2024_2_5_12.csv',
    'EURUSDOTC_2024_2_6_19.csv',
    'EURUSD_2024_2_5_11.csv',
    'EURUSD_2024_2_5_13.csv',
    'EURUSD_2024_2_5_15.csv',
    'EURUSD_2024_2_6_19.csv',
    'GBPUSD_2024_2_5_11.csv',
    'GBPUSD_2024_2_6_19.csv',
    'NZDJPYOTC_2024_2_5_12.csv',
    'NZDJPYOTC_2024_2_6_19.csv',
    'USDCADOTC_2024_2_5_12.csv',
    'USDCADOTC_2024_2_6_19.csv',
    'USDCAD_2024_2_5_11.csv',
    'USDCNH_2024_2_5_11.csv'
  ];

  // Group files by currency pair
  const pairGroups = {};
  availableFiles.forEach(file => {
    const pairName = file.split('_')[0];
    if (!pairGroups[pairName]) {
      pairGroups[pairName] = [];
    }
    pairGroups[pairName].push(file);
  });

  // Create currency pairs array with formatted names
  return Object.keys(pairGroups).map(pairId => {
    const displayName = pairId.replace('OTC', ' OTC').replace(/([A-Z]{3})([A-Z]{3})/, '$1/$2');
    return {
      id: pairId,
      name: displayName,
      file: pairGroups[pairId][0] // Use the first file for each pair
    };
  });
};
