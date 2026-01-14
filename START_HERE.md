# 🚀 START HERE - One Command Setup

## Get Started in 30 Seconds

```bash
./setup.sh
```

This single command will:
1. ✅ Check Python version
2. ✅ Create virtual environment  
3. ✅ Install all dependencies
4. ✅ Set up directory structure
5. ✅ Create configuration files
6. ✅ Verify installation with demo

## After Setup

Run the demo to see it in action:

```bash
./start.sh
```

Or manually:
```bash
source venv/bin/activate
python3 scripts/demo.py
```

## What You'll Get

- ✅ 48 sample product records
- ✅ 2 stores (FL and GA)
- ✅ 4 weeks of data
- ✅ All 10 required variables captured
- ✅ CSV output file ready

## Next Steps

1. **Update `.env`** with your credentials (optional):
   ```bash
   nano .env
   ```

2. **Run the scraper**:
   ```bash
   python3 -m src.publix_scraper.main --week 1 --store-limit 10
   ```

3. **Check the results**:
   ```bash
   cat data/publix_soda_prices.csv
   ```

## Need Help?

- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [INSTALL.md](INSTALL.md) - Detailed installation
- [README.md](README.md) - Full documentation
- [FEATURES.md](FEATURES.md) - All features

---

**That's all you need!** Just run `./setup.sh` and you're ready to go! 🎉
