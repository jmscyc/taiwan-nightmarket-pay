// 日本國內藥妝多店比價模組 (松本清、唐吉訶德、大國等)
const DomesticDrugComparator = {
  STORAGE_KEY: "travel_domestic_drug_records",
  records: [], // [{ id, barcode, name, image, stores: [{ storeName, price, isTaxIncluded, note, photo, date }] }]
  selectedProductId: null,
  currentShelfPhoto: null,
  isBatchMode: false,
  selectedBatchIds: new Set(),

  init() {
    this.loadRecords();
    this.renderCouponList();
    this.bindEvents();
    this.renderProductsList();
  },

  loadRecords() {
    const raw = localStorage.getItem(this.STORAGE_KEY);
    if (raw) {
      try {
        this.records = JSON.parse(raw);
      } catch (e) {
        this.records = [];
      }
    }
    // 如果是空的，預先填入一筆熱門商品範例（方便使用者立即看到效果）
    if (this.records.length === 0 && window.SAMPLE_PRODUCTS) {
      const sample = window.SAMPLE_PRODUCTS.find(p => p.category === "medicine");
      if (sample) {
        this.records.push({
          id: "rec_" + Date.now(),
          barcode: sample.barcode,
          name: sample.name,
          image: sample.image,
          category: sample.category,
          stores: [
            { storeName: "唐吉訶德 澀谷店", price: 5480, isTaxIncluded: true, note: "未退稅標價", date: "今天 10:30" },
            { storeName: "松本清 新宿東口店", price: 4980, isTaxIncluded: false, note: "滿萬再折 5%", date: "今天 13:15" },
            { storeName: "大國藥妝 心齋橋店", price: 4780, isTaxIncluded: false, note: "特惠限購2罐", date: "今天 15:40" }
          ]
        });
        this.saveRecords();
      }
    }
  },

  saveRecords() {
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.records));
  },

  bindEvents() {
    // 新增店家價格
    const addPriceForm = document.getElementById("add-price-form");
    if (addPriceForm) {
      addPriceForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this.handleAddStorePrice();
      });
    }

    // 建立新商品按鈕
    const createProdBtn = document.getElementById("btn-create-drug-prod");
    if (createProdBtn) {
      createProdBtn.addEventListener("click", () => this.showCreateProductModal());
    }
  },

  // 接收條碼掃描
  handleScannedBarcode(barcode) {
    let existing = this.records.find(r => r.barcode === barcode);
    if (!existing) {
      // 檢查是否在預置庫中
      const sample = window.SAMPLE_PRODUCTS.find(p => p.barcode === barcode);
      if (sample) {
        existing = {
          id: "rec_" + Date.now(),
          barcode: sample.barcode,
          name: sample.name,
          image: sample.image,
          category: sample.category,
          stores: []
        };
        this.records.unshift(existing);
        this.saveRecords();
      } else {
        // 未知商品，彈出建立視窗
        this.showCreateProductModal(barcode);
        return;
      }
    }
    this.selectProduct(existing.id);
  },

  showCreateProductModal(barcode = "") {
    const modal = document.getElementById("create-prod-modal");
    document.getElementById("modal-prod-barcode").value = barcode;
    document.getElementById("modal-prod-name").value = "";
    document.getElementById("modal-prod-image").value = "";
    modal.classList.remove("hidden");
  },

  closeCreateProductModal() {
    document.getElementById("create-prod-modal").classList.add("hidden");
  },

  submitCreateProduct(name, barcode, imageUrl) {
    if (!name) {
      alert("請輸入商品名稱");
      return;
    }
    const newProd = {
      id: "rec_" + Date.now(),
      barcode: barcode || ("CUSTOM-" + Math.floor(Math.random() * 899999 + 100000)),
      name: name,
      image: imageUrl || "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&w=400&q=80",
      stores: []
    };
    this.records.unshift(newProd);
    this.saveRecords();
    this.closeCreateProductModal();
    this.renderProductsList();
    this.selectProduct(newProd.id);
  },

  selectProduct(id) {
    this.selectedProductId = id;
    this.renderProductsList();
    this.renderComparisonDetail(id);
  },

  handleAddStorePrice() {
    if (!this.selectedProductId) {
      alert("請先選擇或掃描一個商品！");
      return;
    }
    const storeSelect = document.getElementById("input-store-name");
    const customStore = document.getElementById("input-custom-store").value.trim();
    const storeName = customStore || storeSelect.value;
    const price = parseFloat(document.getElementById("input-store-price").value);
    const isTaxIncluded = document.getElementById("input-tax-included").checked;
    const note = document.getElementById("input-store-note").value.trim();

    if (!storeName || isNaN(price) || price <= 0) {
      alert("請輸入有效的店家名稱與日圓價格！");
      return;
    }

    const prod = this.records.find(r => r.id === this.selectedProductId);
    if (!prod) return;

    // 將既有的同店家紀錄更新，或新增
    const nowStr = new Date().toLocaleTimeString("zh-TW", { hour: "2-digit", minute: "2-digit" });
    const existingStoreIndex = prod.stores.findIndex(s => s.storeName === storeName);
    
    const storeData = {
      storeName,
      price,
      isTaxIncluded,
      note,
      photo: this.currentShelfPhoto || null,
      date: nowStr
    };

    if (existingStoreIndex >= 0) {
      prod.stores[existingStoreIndex] = storeData;
    } else {
      prod.stores.push(storeData);
    }

    this.saveRecords();
    document.getElementById("input-store-price").value = "";
    document.getElementById("input-custom-store").value = "";
    document.getElementById("input-store-note").value = "";
    this.clearSelectedPhoto();

    this.renderComparisonDetail(prod.id);
  },

  // 照片拍照處理 (壓縮成縮圖 base64 存入 localStorage 防止過大)
  handleShelfPhotoSelected(inputEl) {
    if (!inputEl.files || inputEl.files.length === 0) return;
    const file = inputEl.files[0];
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement("canvas");
        const maxDim = 800; // 最寬或最高 800px 節省容量
        let w = img.width;
        let h = img.height;
        if (w > maxDim || h > maxDim) {
          if (w > h) {
            h = Math.round((h * maxDim) / w);
            w = maxDim;
          } else {
            w = Math.round((w * maxDim) / h);
            h = maxDim;
          }
        }
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0, w, h);
        const compressedBase64 = canvas.toDataURL("image/jpeg", 0.7);

        this.currentShelfPhoto = compressedBase64;
        document.getElementById("shelf-photo-thumb").src = compressedBase64;
        document.getElementById("shelf-photo-preview-wrap").classList.remove("hidden");
        document.getElementById("shelf-photo-label").textContent = "已拍存證照 (點擊可重拍)";
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  },

  clearSelectedPhoto() {
    this.currentShelfPhoto = null;
    const thumb = document.getElementById("shelf-photo-thumb");
    if (thumb) thumb.src = "";
    const wrap = document.getElementById("shelf-photo-preview-wrap");
    if (wrap) wrap.classList.add("hidden");
    const label = document.getElementById("shelf-photo-label");
    if (label) label.textContent = "拍貨架標籤 (存證防混淆)";
    const fileInput = document.getElementById("input-shelf-photo");
    if (fileInput) fileInput.value = "";
  },

  viewPhoto(src) {
    if (!src) return;
    document.getElementById("photo-viewer-img").src = src;
    document.getElementById("photo-viewer-modal").classList.remove("hidden");
  },

  closePhotoViewer() {
    document.getElementById("photo-viewer-modal").classList.add("hidden");
  },

  // 批次刪除與清空資料功能
  toggleBatchMode(force = null) {
    this.isBatchMode = force !== null ? force : !this.isBatchMode;
    const bar = document.getElementById("batch-delete-bar");
    if (bar) {
      if (this.isBatchMode) {
        bar.classList.remove("hidden");
      } else {
        bar.classList.add("hidden");
        this.selectedBatchIds.clear();
      }
    }
    this.renderProductsList();
  },

  toggleBatchSelect(prodId, isChecked) {
    if (isChecked) {
      this.selectedBatchIds.add(prodId);
    } else {
      this.selectedBatchIds.delete(prodId);
    }
  },

  executeBatchDelete() {
    if (this.selectedBatchIds.size === 0) {
      alert("請先勾選要刪除的商品！");
      return;
    }
    if (!confirm(`確定要刪除選取的 ${this.selectedBatchIds.size} 項商品比價記錄嗎？`)) {
      return;
    }
    this.records = this.records.filter(r => !this.selectedBatchIds.has(r.id));
    this.saveRecords();
    this.selectedBatchIds.clear();
    this.toggleBatchMode(false);
    this.selectedProductId = this.records.length > 0 ? this.records[0].id : null;
    this.renderProductsList();
    if (this.selectedProductId) {
      this.renderComparisonDetail(this.selectedProductId);
    } else {
      document.getElementById("drug-detail-view").classList.add("hidden");
      document.getElementById("drug-empty-view").classList.remove("hidden");
    }
  },

  clearAllRecords() {
    if (!confirm("⚠️ 警告：這將會清除「所有已記錄的藥妝比價資料」，確定要全部清空嗎？")) {
      return;
    }
    this.records = [];
    this.saveRecords();
    this.selectedBatchIds.clear();
    this.toggleBatchMode(false);
    this.selectedProductId = null;
    this.renderProductsList();
    document.getElementById("drug-detail-view").classList.add("hidden");
    document.getElementById("drug-empty-view").classList.remove("hidden");
  },

  deleteStorePrice(prodId, storeIndex) {
    const prod = this.records.find(r => r.id === prodId);
    if (prod && prod.stores[storeIndex]) {
      prod.stores.splice(storeIndex, 1);
      this.saveRecords();
      this.renderComparisonDetail(prodId);
    }
  },

  deleteProduct(prodId) {
    if (!confirm("確定要刪除此商品的全部比價記錄嗎？")) return;
    this.records = this.records.filter(r => r.id !== prodId);
    this.saveRecords();
    this.selectedProductId = this.records.length > 0 ? this.records[0].id : null;
    this.renderProductsList();
    if (this.selectedProductId) {
      this.renderComparisonDetail(this.selectedProductId);
    } else {
      document.getElementById("drug-detail-view").classList.add("hidden");
      document.getElementById("drug-empty-view").classList.remove("hidden");
    }
  },

  // 渲染所有已記錄商品清單 (頂部滑動卡片)
  renderProductsList() {
    const container = document.getElementById("drug-prod-chips");
    if (!container) return;

    if (this.records.length === 0) {
      container.innerHTML = `<span class="text-xs text-gray-400">尚未記錄任何商品，請掃碼或點擊＋新增</span>`;
      return;
    }

    container.innerHTML = this.records.map(prod => {
      const isSelected = prod.id === this.selectedProductId;
      const count = prod.stores.length;
      const isChecked = this.selectedBatchIds.has(prod.id);

      if (this.isBatchMode) {
        return `
          <label class="flex-shrink-0 flex items-center space-x-1.5 px-3 py-1.5 rounded-full border text-xs font-medium cursor-pointer ${
            isChecked ? 'bg-rose-100 border-rose-500 text-rose-800' : 'bg-white border-slate-200 text-slate-700'
          }">
            <input type="checkbox" ${isChecked ? 'checked' : ''} onchange="DomesticDrugComparator.toggleBatchSelect('${prod.id}', this.checked)" class="rounded text-rose-600">
            <span class="truncate max-w-[110px]">${prod.name}</span>
            <span class="text-[10px] text-slate-400">(${count}店)</span>
          </label>
        `;
      }

      return `
        <button onclick="DomesticDrugComparator.selectProduct('${prod.id}')"
          class="flex-shrink-0 flex items-center space-x-2 px-3 py-1.5 rounded-full border text-xs font-medium transition-all ${
            isSelected 
              ? 'bg-rose-600 text-white border-rose-600 shadow-sm' 
              : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50'
          }">
          <span class="truncate max-w-[110px]">${prod.name}</span>
          <span class="px-1.5 py-0.2 rounded-full text-[10px] ${isSelected ? 'bg-rose-800 text-white' : 'bg-gray-100 text-gray-600'}">${count}店</span>
        </button>
      `;
    }).join("");
  },

  // 渲染目前選中商品的各店比價排行榜
  renderComparisonDetail(prodId) {
    const prod = this.records.find(r => r.id === prodId);
    const detailView = document.getElementById("drug-detail-view");
    const emptyView = document.getElementById("drug-empty-view");

    if (!prod) {
      detailView.classList.add("hidden");
      emptyView.classList.remove("hidden");
      return;
    }

    detailView.classList.remove("hidden");
    emptyView.classList.add("hidden");

    // 基本資訊
    document.getElementById("drug-prod-name").textContent = prod.name;
    document.getElementById("drug-prod-barcode").textContent = `條碼: ${prod.barcode || '無'}`;
    document.getElementById("drug-prod-img").src = prod.image || "https://placehold.co/400x400?text=藥妝";
    
    // 快速搜尋官方比價
    const searchA = document.getElementById("drug-web-search");
    if (searchA) {
      searchA.href = `https://www.google.com/search?q=${encodeURIComponent(prod.name)}+藥妝+比價`;
    }

    const rate = CurrencyManager.getRate();

    // 排序各店價格：換算未稅等效基準比較
    // 假設外國人買滿 5000 円可退稅，若標示含稅則除以 1.1 換算為稅前基礎比較
    const normalizedStores = prod.stores.map((s, idx) => {
      const netPrice = s.isTaxIncluded ? Math.round(s.price / 1.1) : s.price;
      const twd = Math.round(netPrice * rate);
      return { ...s, netPrice, twd, originalIndex: idx };
    }).sort((a, b) => a.netPrice - b.netPrice);

    const lowestNetPrice = normalizedStores.length > 0 ? normalizedStores[0].netPrice : 0;
    const highestNetPrice = normalizedStores.length > 0 ? normalizedStores[normalizedStores.length - 1].netPrice : 0;
    const maxDiffJpy = highestNetPrice - lowestNetPrice;
    const maxDiffTwd = Math.round(maxDiffJpy * rate);

    // 頂部最優推薦提示
    const bestBanner = document.getElementById("drug-best-banner");
    if (normalizedStores.length >= 2 && maxDiffJpy > 0) {
      bestBanner.classList.remove("hidden");
      bestBanner.innerHTML = `
        <div class="flex items-center justify-between text-xs sm:text-sm">
          <span>🏆 <strong>${normalizedStores[0].storeName}</strong> 最便宜！</span>
          <span class="font-bold text-rose-600">最高立省 ¥${maxDiffJpy.toLocaleString()} (約 NT$ ${maxDiffTwd})</span>
        </div>
      `;
    } else {
      bestBanner.classList.add("hidden");
    }

    // 表格內容
    const tableBody = document.getElementById("drug-stores-table-body");
    if (normalizedStores.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="4" class="text-center py-6 text-gray-400 text-xs">這間商品還沒有輸入店家價格，請在下方快速記錄！</td></tr>`;
      return;
    }

    tableBody.innerHTML = normalizedStores.map((s, rank) => {
      const isLowest = rank === 0;
      const isHighest = rank === normalizedStores.length - 1 && normalizedStores.length > 1;
      const diffFromBest = s.netPrice - lowestNetPrice;

      return `
        <tr class="border-b border-gray-100 ${isLowest ? 'bg-emerald-50/70 font-semibold' : ''}">
          <td class="py-3 px-2">
            <div class="flex items-center space-x-1.5">
              ${isLowest ? '<span class="text-xs px-1.5 py-0.5 rounded bg-emerald-600 text-white font-bold">最低</span>' : `<span class="text-xs text-gray-400 font-mono">#${rank+1}</span>`}
              <div>
                <div class="text-sm font-medium text-gray-800 flex items-center gap-1.5">
                  <span>${s.storeName}</span>
                  ${s.photo ? `
                    <button onclick="DomesticDrugComparator.viewPhoto('${s.photo}')" class="px-1.5 py-0.5 rounded bg-indigo-50 border border-indigo-200 text-indigo-700 text-[10px] font-bold hover:bg-indigo-100 flex items-center gap-0.5">
                      📷 貨架照
                    </button>
                  ` : ''}
                </div>
                ${s.note ? `<div class="text-[11px] text-gray-500">${s.note}</div>` : ''}
              </div>
            </div>
          </td>
          <td class="py-3 px-2 text-right">
            <div class="text-sm font-bold ${isLowest ? 'text-emerald-700' : 'text-gray-900'}">
              ¥${s.price.toLocaleString()}
            </div>
            <div class="text-[10px] text-gray-400">
              ${s.isTaxIncluded ? '含稅' : '未稅'} · 免稅等效: ¥${s.netPrice.toLocaleString()}
            </div>
          </td>
          <td class="py-3 px-2 text-right">
            <div class="text-xs font-semibold text-gray-700">NT$ ${s.twd.toLocaleString()}</div>
            ${diffFromBest > 0 ? `<div class="text-[10px] text-rose-500 font-medium">+¥${diffFromBest}</div>` : '<div class="text-[10px] text-emerald-600 font-medium">最划算</div>'}
          </td>
          <td class="py-3 px-1 text-center">
            <button onclick="DomesticDrugComparator.deleteStorePrice('${prod.id}', ${s.originalIndex})" class="text-gray-300 hover:text-rose-500 text-xs p-1">
              ✕
            </button>
          </td>
        </tr>
      `;
    }).join("");
  },

  // 渲染各大藥妝最新折價券/活動
  renderCouponList() {
    const list = document.getElementById("drug-coupons-carousel");
    if (!list || !window.DRUGSTORE_COUPONS) return;

    list.innerHTML = window.DRUGSTORE_COUPONS.map(c => `
      <div class="min-w-[240px] max-w-[260px] flex-shrink-0 bg-white rounded-xl border border-gray-100 p-3 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
        <div class="h-1.5 w-full bg-gradient-to-r ${c.bgColor} absolute top-0 left-0"></div>
        <div class="flex items-center justify-between mb-1">
          <span class="text-xs font-bold text-gray-800">${c.store}</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-rose-50 text-rose-600 font-bold">${c.tag}</span>
        </div>
        <p class="text-[11px] text-gray-600 line-clamp-2 leading-relaxed mb-2">${c.desc}</p>
        <div class="flex items-center justify-between pt-1 border-t border-gray-50 text-[10px]">
          <span class="text-gray-400">${c.validDate}</span>
          <a href="${c.url}" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline font-semibold flex items-center">
            領取活動券 ↗
          </a>
        </div>
      </div>
    `).join("");
  }
};

window.DomesticDrugComparator = DomesticDrugComparator;
