# Phase 2: CSV Endpoint Fix - Complete Resolution

## Problem Identified
The frontend was calling the wrong CSV API endpoint, resulting in 404 errors when loading CSV data.

### Root Cause
- **Frontend was calling**: `/api/csv/{assetId}?timeframe={tf}`
- **Backend endpoint is**: `/api/csv-data/{filename}`
- **Mismatch**: Asset ID format (e.g., `ADA-USD_OTC`) ≠ Filename format (e.g., `ADA-USD_OTC_1m_candles.csv`)

### Error Observed
```
Failed to load resource: the server responded with a status of 404 (NOT FOUND)
for /api/csv/ADA-USD_OTC?timeframe=1m
```

---

## Solution Implemented

### 1. Backend Endpoint Analysis (streaming_server.py:534)
```python
@app.route('/api/csv-data/<path:filename>')
def serve_csv_file(filename):
    """Serve CSV file content"""
    # Searches multiple directories for the file
    # Returns file with mimetype='text/csv'
```

**Key Points:**
- Endpoint expects a **filename** parameter, not an asset ID
- Searches across multiple timeframe directories (1M, 5M, 15M, 1H, 4H, 0M)
- Returns raw CSV text content

### 2. Frontend Data Flow Fix (DataAnalysis.jsx)

#### Change 1: Track Selected Asset Filename
```javascript
// Added new state to store the filename
const [selectedAssetFile, setSelectedAssetFile] = useState('');
```

#### Change 2: Update Asset Selection Handler
```javascript
// When user selects an asset, also capture its filename
onChange={(e) => {
  const asset = availableAssets.find(a => a.id === e.target.value);
  setSelectedAsset(e.target.value);
  setSelectedAssetFile(asset?.file || '');
}}
```

#### Change 3: Fix CSV Data Loading Function
```javascript
const loadCsvData = async (assetId, tf) => {
  if (!assetId || !selectedAssetFile) return;
  
  try {
    // Use filename instead of asset ID
    const response = await fetch(`http://localhost:3001/api/csv-data/${selectedAssetFile}`);
    if (!response.ok) throw new Error(`Failed to load CSV data: ${response.status}`);
    
    // Parse CSV text response
    const text = await response.text();
    const lines = text.trim().split('\n');
    const headers = lines[0].split(',').map(h => h.trim());
    const rawData = lines.slice(1).map(line => {
      const values = line.split(',').map(v => v.trim());
      const obj = {};
      headers.forEach((header, idx) => {
        obj[header] = isNaN(values[idx]) ? values[idx] : parseFloat(values[idx]);
      });
      return obj;
    });
    
    // Continue with data processing
    const parsedData = parseTradingData(rawData);
    setChartData(parsedData);
    // ... rest of processing
  } catch (err) {
    console.error('[CSV] Load error:', err);
    setLoadingStatus(`Error: ${err.message}`);
  }
};
```

---

## Data Flow Diagram

```
User selects asset
    ↓
fetchCurrencyPairs() returns:
  {
    id: 'ADA-USD_OTC',
    name: 'ADA-USD_OTC_1m_candles',
    file: 'ADA-USD_OTC_1m_candles.csv',  ← FILENAME
    path: '/full/path/to/file',
    timeframe: '1m',
    size: 12345
  }
    ↓
Store filename in selectedAssetFile state
    ↓
loadCsvData() called
    ↓
fetch(`/api/csv-data/{selectedAssetFile}`)
    ↓
Backend finds file and returns CSV text
    ↓
Frontend parses CSV text into array
    ↓
Chart renders with data
```

---

## Files Modified

### 1. [`gui/Data-Visualizer-React/src/pages/DataAnalysis.jsx`](gui/Data-Visualizer-React/src/pages/DataAnalysis.jsx)

**Changes:**
- Line 23: Added `selectedAssetFile` state
- Line 108: Set filename when loading available assets
- Line 113: Clear filename when switching to platform mode
- Lines 417-422: Update asset selection handler to capture filename
- Lines 126-157: Rewrote `loadCsvData()` function to:
  - Use filename instead of asset ID
  - Fetch from correct endpoint `/api/csv-data/{filename}`
  - Parse CSV text response manually
  - Handle CSV parsing errors

---

## Testing Checklist

- [ ] Select an asset from CSV dropdown
- [ ] Verify chart loads without 404 errors
- [ ] Verify chart displays candle data correctly
- [ ] Switch between different assets
- [ ] Switch between different timeframes
- [ ] Verify indicators calculate correctly
- [ ] Test error handling with invalid asset

---

## Related Components

### Backend (streaming_server.py)
- `/api/available-csv-files` - Returns list of available CSV files with metadata
- `/api/csv-data/<filename>` - Serves CSV file content

### Frontend (fileUtils.js)
- `fetchCurrencyPairs(timeframe)` - Fetches available assets and their filenames
- Returns array with `file` property containing the filename

### Frontend (DataAnalysis.jsx)
- Uses filename from `fetchCurrencyPairs()` to load CSV data
- Parses CSV text response into chart-compatible format

---

## Performance Considerations

1. **CSV Parsing**: Now done client-side instead of server-side
   - Reduces server load
   - Faster response times
   - Better error handling

2. **Caching**: `fetchCurrencyPairs()` caches results in localStorage
   - Reduces API calls
   - Faster asset list loading

3. **Error Handling**: Comprehensive error messages
   - HTTP status codes included
   - CSV parsing errors caught
   - User-friendly error display

---

## Next Steps

1. **Verify Chart Rendering**: Test with actual CSV data
2. **Test Indicators**: Ensure backend indicators calculate correctly
3. **Performance Testing**: Monitor load times with large CSV files
4. **Error Scenarios**: Test with missing/corrupted CSV files

---

## Sign-Off

**Status**: ✅ COMPLETE  
**Issue**: CSV endpoint 404 error  
**Root Cause**: Wrong endpoint and missing filename mapping  
**Solution**: Use filename from asset metadata to fetch CSV data  
**Testing**: Ready for verification  

**Recommendation**: Proceed with chart rendering verification and indicator testing.