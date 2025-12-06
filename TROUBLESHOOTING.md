# Troubleshooting Guide

## Installation Steps

1. **Copy the integration to Home Assistant:**
   ```bash
   # Copy the entire trv_manager folder to your custom_components directory
   cp -r custom_components/trv_manager /path/to/homeassistant/config/custom_components/
   ```

2. **Restart Home Assistant:**
   - Go to Developer Tools → YAML → Restart (or restart the container/service)
   - Wait for Home Assistant to fully restart

3. **Clear browser cache:**
   - Press Ctrl+Shift+R (or Cmd+Shift+R on Mac)
   - Or clear your browser cache completely

4. **Check logs:**
   - Go to Settings → System → Logs
   - Look for any errors related to `trv_manager`

5. **Add the integration:**
   - Go to Settings → Devices & Services
   - Click "+ ADD INTEGRATION"
   - Search for "TRV Manager"

## Common Issues

### "Config flow could not be loaded: Invalid handler specified"

**Causes:**
- Integration not properly copied to custom_components folder
- Home Assistant hasn't detected the integration yet
- Browser cache showing old version

**Solutions:**
1. Verify the integration is in the correct location:
   ```
   /config/custom_components/trv_manager/
   ├── __init__.py
   ├── config_flow.py
   ├── const.py
   ├── coordinator.py
   ├── manifest.json
   ├── number.py
   ├── sensor.py
   ├── strings.json
   └── translations/
       └── en.json
   ```

2. Restart Home Assistant completely (not just reload)

3. Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)

4. Check Home Assistant logs for import errors:
   ```
   Settings → System → Logs
   ```

5. Try accessing Home Assistant in an incognito/private browsing window

### "Blocking call to import_module" warning

This is a warning, not an error. It occurs during development and doesn't prevent the integration from working. It will be resolved in future Home Assistant versions.

### Integration not appearing in the list

**Solutions:**
1. Verify `manifest.json` exists and is valid JSON
2. Check that `config_flow.py` has no syntax errors
3. Restart Home Assistant and clear cache
4. Check the file permissions (should be readable)

### Config flow loads but shows errors

**Check:**
1. Do you have at least one climate entity in your system?
2. Do you have at least one temperature sensor?
3. Do you have a target temperature entity (sensor, input_number, or number)?

## Verification Steps

### 1. Check Integration Files
```bash
# From your Home Assistant config directory
ls -la custom_components/trv_manager/
```

You should see all the files listed above.

### 2. Check for Syntax Errors
Look in the Home Assistant logs:
```
Settings → System → Logs
```

Filter by "trv_manager" to see only relevant messages.

### 3. Test Import
You can test if Python can import the integration:
```bash
# From Home Assistant container/environment
python3 -c "from custom_components.trv_manager import config_flow"
```

If this shows an error, there's a syntax problem in config_flow.py.

### 4. Verify Manifest
Check the manifest is valid JSON:
```bash
cat custom_components/trv_manager/manifest.json | python3 -m json.tool
```

## After Fixing Issues

1. Delete `__pycache__` folders:
   ```bash
   find custom_components/trv_manager -type d -name __pycache__ -exec rm -rf {} +
   ```

2. Restart Home Assistant completely

3. Clear browser cache

4. Try adding the integration again

## Getting Help

If issues persist, check:
1. Home Assistant version (integration requires 2023.8+)
2. Python version (requires 3.11+)
3. All files are present and readable
4. No special characters in file paths
5. File permissions are correct

Include the following in bug reports:
- Home Assistant version
- Full error message from logs
- Output of `ls -la custom_components/trv_manager/`
- Contents of manifest.json

