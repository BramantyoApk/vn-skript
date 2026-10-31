# Commands & RCON Execution

## Command Mapping Penting
- **Reload BetterHUD via RCON**:
  `python tools/send_rcon.py "vn reloadhud"`
  *(Dilarang: `hud reload` via RCON karena `RemoteConsoleCommandSender` dipetakan ke null).*
- **Send Test Dialog**:
  `python tools/send_rcon.py "dialog send Bramanzero Luna Halo selamat datang!"`
- **Recompile Pipeline & Sync Client Pack**:
  `python tools/compiler.py`
  `python -c "import sys; sys.path.insert(0, 'tools'); from compiler import sync_client_pack; print(sync_client_pack())"`
- **Test Cutscene / Full Story**:
  `python tools/send_rcon.py "vn test"`
