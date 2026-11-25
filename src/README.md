# Robot software

The display and voice loop live in the `robot_display` package.

```bash
# From the project folder, after src is on PYTHONPATH:
python3 -m robot_display

# Laptop shortcut:
python3 run_simulator.py
python3 run_simulator.py --demo
```

Hold V to talk if a microphone and `XAI_API_KEY` are set. Press T for a visual mode demo that needs no mic or key.

Keep secrets in a local `.env` file. Never commit that file.
