# 🚀 Crawler Quick Start - Command Order

## **Run These Commands In Order:**

### **1. Install Dependencies** ⚙️
```bash
pip3 install httpx beautifulsoup4 pyyaml
```

### **2. Test Components** 🧪
```bash
python3 -m scripts.crawler.cli test
```

### **3. Small Test (1 bank, 5 PDFs)** 🏃
```bash
python3 -m scripts.crawler.cli crawl --domain chase.com --max-pdfs 5 --verbose
```

### **4. Check Test Results** 📊
```bash
cat out/crawler_report.json | jq '.summary'
ls -la tests/fixtures/pdf/features/crawled/
```

### **5. Full Crawl (All banks, 50 PDFs)** 🚀
```bash
python3 -m scripts.crawler.cli crawl --max-pdfs 50 --verbose
```

### **6. Review Results** 📈
```bash
cat out/crawler_report.json | jq '.summary'

for dir in tests/fixtures/pdf/features/crawled/*/; do
  bank=$(basename "$dir")
  count=$(ls -1 "$dir"*.json 2>/dev/null | wc -l)
  echo "$bank: $count features"
done
```

---

## **Expected Timeline:**

- Step 1: 30 seconds
- Step 2: 10 seconds
- Step 3: 2-5 minutes
- Step 4: Instant
- Step 5: 15-30 minutes
- Step 6: Instant

---

## **What You'll Get:**

After Step 5 completes:
- ✅ 15-20 banks discovered
- ✅ 50+ PDF features extracted
- ✅ Ready to create templates
- ✅ 70%+ market coverage

---

## **Troubleshooting:**

**Command not found?**
- Use `python3` not `python`
- Use `pip3` not `pip`

**No PDFs found?**
- Normal for some banks
- Check `out/crawler_report.json` for reasons

**Timeout errors?**
- Normal, some banks slow
- Crawler continues with other banks

---

## **Full Documentation:**

- Complete Guide: `docs/CRAWLER_README.md`
- Completion Report: `CRAWLER_COMPLETE.md`



