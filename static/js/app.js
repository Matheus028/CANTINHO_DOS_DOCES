// Balas Baianas Management System - JavaScript Functions
// This file contains reusable JavaScript functions for the entire application

// Global variables
let lastCalculationTime = 0;
const CALCULATION_DEBOUNCE = 300; // ms

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    // Initialize Bootstrap tooltips
    initializeTooltips();
    
    // Initialize form validations
    initializeFormValidation();
    
    // Initialize auto-save features
    initializeAutoSave();
    
    // Initialize calculations
    initializeCalculations();
    
    // Initialize navigation enhancements
    initializeNavigation();
    
    console.log('Balas Baianas Management System initialized');
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Focus on first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * Initialize auto-save functionality
 */
function initializeAutoSave() {
    const autoSaveInputs = document.querySelectorAll('[data-auto-save]');
    
    autoSaveInputs.forEach(input => {
        input.addEventListener('change', debounce(function() {
            saveFieldValue(input);
        }, 1000));
    });
}

/**
 * Initialize calculation functions
 */
function initializeCalculations() {
    // Production capacity calculations
    initializeProductionCalculations();
    
    // Sales calculations
    initializeSalesCalculations();
    
    // Financial calculations
    initializeFinancialCalculations();
}

/**
 * Initialize navigation enhancements
 */
function initializeNavigation() {
    // Add active class to current page
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
    
    // Add confirmation to destructive actions
    const destructiveButtons = document.querySelectorAll('[data-confirm]');
    destructiveButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
}

/**
 * Production capacity calculations
 */
function initializeProductionCalculations() {
    const sociaProdutora = document.getElementById('sociaProdutora');
    const receitaId = document.getElementById('receitaId');
    
    if (sociaProdutora && receitaId) {
        [sociaProdutora, receitaId].forEach(element => {
            element.addEventListener('change', updateProductionCapacity);
        });
    }
}

/**
 * Sales calculations
 */
function initializeSalesCalculations() {
    const canalVenda = document.getElementById('canalVenda');
    if (canalVenda) {
        canalVenda.addEventListener('change', updateSalesOptions);
    }
}

/**
 * Financial calculations
 */
function initializeFinancialCalculations() {
    const financialInputs = document.querySelectorAll('.financial-input');
    financialInputs.forEach(input => {
        input.addEventListener('input', debounce(updateFinancialSummary, CALCULATION_DEBOUNCE));
    });
}

/**
 * Update production capacity display
 */
function updateProductionCapacity() {
    const socia = document.getElementById('sociaProdutora')?.value;
    const receitaId = document.getElementById('receitaId')?.value;
    
    if (!socia || !receitaId) {
        hideCapacityInfo();
        return;
    }
    
    showLoading('capacidadeInfo');
    
    fetch(`/api/capacidade/${socia}?receita_id=${receitaId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            displayCapacityInfo(data);
        })
        .catch(error => {
            console.error('Error fetching capacity:', error);
            showError('Erro ao calcular capacidade de produção');
            hideCapacityInfo();
        })
        .finally(() => {
            hideLoading('capacidadeInfo');
        });
}

/**
 * Display capacity information
 */
function displayCapacityInfo(data) {
    const capacidadeInfo = document.getElementById('capacidadeInfo');
    const capacidadeDetalhes = document.getElementById('capacidadeDetalhes');
    
    if (!capacidadeInfo || !capacidadeDetalhes) return;
    
    if (data.receitas > 0) {
        capacidadeDetalhes.innerHTML = `
            <div class="row">
                <div class="col-6">
                    <strong class="text-success">${data.receitas}</strong> receitas
                </div>
                <div class="col-6">
                    <strong class="text-primary">${data.balas}</strong> balas
                </div>
            </div>
            <small class="text-muted">Capacidade máxima com estoque atual</small>
        `;
        capacidadeInfo.className = 'alert alert-success capacity-indicator';
        
        // Update input max value
        const receitasProduzir = document.getElementById('receitasProduzir');
        if (receitasProduzir) {
            receitasProduzir.max = data.receitas;
        }
    } else {
        capacidadeDetalhes.innerHTML = `
            <div class="text-center">
                <i class="fas fa-exclamation-triangle text-warning"></i>
                <strong class="text-warning">Estoque insuficiente</strong>
                <br><small class="text-muted">Verifique o estoque de ingredientes</small>
            </div>
        `;
        capacidadeInfo.className = 'alert alert-warning capacity-indicator';
        
        // Set input max to 0
        const receitasProduzir = document.getElementById('receitasProduzir');
        if (receitasProduzir) {
            receitasProduzir.max = 0;
            receitasProduzir.value = '';
        }
    }
    
    capacidadeInfo.style.display = 'block';
}

/**
 * Hide capacity information
 */
function hideCapacityInfo() {
    const capacidadeInfo = document.getElementById('capacidadeInfo');
    if (capacidadeInfo) {
        capacidadeInfo.style.display = 'none';
    }
}

/**
 * Update sales options based on channel
 */
function updateSalesOptions() {
    const canal = document.getElementById('canalVenda')?.value;
    
    // Hide all options first
    hideElement('opcoes-restaurante');
    hideElement('opcoes-pacotes');
    hideElement('info-ifood');
    hideElement('resumo-venda');
    
    if (!canal) return;
    
    if (canal === 'restaurante') {
        showElement('opcoes-restaurante');
        setupRestaurantOptions();
    } else {
        showElement('opcoes-pacotes');
        setupPackageOptions(canal);
        
        if (canal === 'ifood') {
            showElement('info-ifood');
        }
    }
}

/**
 * Setup restaurant sales options
 */
function setupRestaurantOptions() {
    const quantidadeInput = document.querySelector('input[name="quantidade_balas"]');
    if (quantidadeInput) {
        quantidadeInput.addEventListener('input', debounce(calculateSalesSummary, CALCULATION_DEBOUNCE));
    }
    
    // Update unit price display if available
    updateUnitPriceDisplay();
}

/**
 * Setup package sales options
 */
function setupPackageOptions(canal) {
    const tipoPacote = document.getElementById('tipoPacote');
    if (!tipoPacote) return;
    
    // Clear existing options
    tipoPacote.innerHTML = '<option value="">Selecione o pacote...</option>';
    
    // Fetch prices for the channel
    fetch(`/api/precos/${canal}`)
        .then(response => response.json())
        .then(precos => {
            Object.entries(precos).forEach(([pacote, preco]) => {
                if (pacote !== 'preco_unitario') {
                    const option = document.createElement('option');
                    option.value = pacote;
                    option.textContent = formatPackageName(pacote, preco);
                    option.dataset.preco = preco;
                    option.dataset.quantidade = extractQuantityFromPackage(pacote);
                    tipoPacote.appendChild(option);
                }
            });
            
            // Add event listener
            tipoPacote.addEventListener('change', calculateSalesSummary);
        })
        .catch(error => {
            console.error('Error fetching prices:', error);
            showError('Erro ao carregar preços');
        });
}

/**
 * Calculate and display sales summary
 */
function calculateSalesSummary() {
    const now = Date.now();
    if (now - lastCalculationTime < CALCULATION_DEBOUNCE) {
        return;
    }
    lastCalculationTime = now;
    
    const canal = document.getElementById('canalVenda')?.value;
    if (!canal) {
        hideElement('resumo-venda');
        return;
    }
    
    let totalBalas = 0;
    let valorBruto = 0;
    
    if (canal === 'restaurante') {
        const quantidade = parseInt(document.querySelector('input[name="quantidade_balas"]')?.value) || 0;
        const precoUnitario = getRestaurantUnitPrice();
        
        totalBalas = quantidade;
        valorBruto = quantidade * precoUnitario;
    } else {
        const tipoPacoteSelect = document.getElementById('tipoPacote');
        const selectedOption = tipoPacoteSelect?.selectedOptions[0];
        
        if (selectedOption?.value) {
            valorBruto = parseFloat(selectedOption.dataset.preco) || 0;
            totalBalas = parseInt(selectedOption.dataset.quantidade) || 0;
        }
    }
    
    if (totalBalas > 0 && valorBruto > 0) {
        displaySalesSummary(totalBalas, valorBruto, canal);
    } else {
        hideElement('resumo-venda');
    }
}

/**
 * Display sales summary
 */
function displaySalesSummary(totalBalas, valorBruto, canal) {
    const custoEstimado = totalBalas * 1.0; // Default cost per candy
    let lucroLiquido = valorBruto - custoEstimado;
    
    // Apply iFood fees
    if (canal === 'ifood') {
        const taxaPercentual = valorBruto * 0.262;
        const taxaFixa = valorBruto < 20.00 ? 1.00 : 0.00;
        const valorLiquido = valorBruto - taxaPercentual - taxaFixa;
        lucroLiquido = valorLiquido - custoEstimado;
    }
    
    // Update summary display
    updateElementText('total-balas', totalBalas);
    updateElementText('valor-bruto', formatCurrency(valorBruto));
    updateElementText('custo-estimado', formatCurrency(custoEstimado));
    updateElementText('lucro-liquido', formatCurrency(lucroLiquido));
    
    // Show profit color
    const lucroElement = document.getElementById('lucro-liquido');
    if (lucroElement) {
        lucroElement.className = lucroLiquido >= 0 ? 'text-success' : 'text-danger';
    }
    
    showElement('resumo-venda');
}

/**
 * Update financial summary
 */
function updateFinancialSummary() {
    // This function can be expanded to calculate real-time financial summaries
    console.log('Updating financial summary...');
}

/**
 * Utility Functions
 */

/**
 * Show loading indicator
 */
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.add('loading');
    }
}

/**
 * Hide loading indicator
 */
function hideLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.classList.remove('loading');
    }
}

/**
 * Show element
 */
function showElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'block';
    }
}

/**
 * Hide element
 */
function hideElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'none';
    }
}

/**
 * Update element text content
 */
function updateElementText(elementId, text) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = text;
    }
}

/**
 * Show error message
 */
function showError(message) {
    // Create or update error alert
    let errorAlert = document.getElementById('error-alert');
    
    if (!errorAlert) {
        errorAlert = document.createElement('div');
        errorAlert.id = 'error-alert';
        errorAlert.className = 'alert alert-danger alert-dismissible fade show';
        errorAlert.innerHTML = `
            <i class="fas fa-exclamation-circle"></i>
            <span id="error-message"></span>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at top of main container
        const container = document.querySelector('.container');
        if (container && container.firstChild) {
            container.insertBefore(errorAlert, container.firstChild);
        }
    }
    
    document.getElementById('error-message').textContent = message;
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        if (errorAlert) {
            errorAlert.remove();
        }
    }, 5000);
}

/**
 * Show success message
 */
function showSuccess(message) {
    // Similar to showError but with success styling
    let successAlert = document.getElementById('success-alert');
    
    if (!successAlert) {
        successAlert = document.createElement('div');
        successAlert.id = 'success-alert';
        successAlert.className = 'alert alert-success alert-dismissible fade show';
        successAlert.innerHTML = `
            <i class="fas fa-check-circle"></i>
            <span id="success-message"></span>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container');
        if (container && container.firstChild) {
            container.insertBefore(successAlert, container.firstChild);
        }
    }
    
    document.getElementById('success-message').textContent = message;
    
    setTimeout(() => {
        if (successAlert) {
            successAlert.remove();
        }
    }, 3000);
}

/**
 * Format currency value
 */
function formatCurrency(value) {
    return value.toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

/**
 * Format package name for display
 */
function formatPackageName(pacote, preco) {
    const formatted = pacote.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    return `${formatted} - R$ ${formatCurrency(preco)}`;
}

/**
 * Extract quantity from package name
 */
function extractQuantityFromPackage(pacote) {
    const match = pacote.match(/(\d+)/);
    return match ? match[1] : '1';
}

/**
 * Get restaurant unit price (placeholder - should be dynamic)
 */
function getRestaurantUnitPrice() {
    const precoElement = document.getElementById('preco-unitario');
    return precoElement ? parseFloat(precoElement.textContent) : 2.50;
}

/**
 * Update unit price display
 */
function updateUnitPriceDisplay() {
    // This should fetch the actual unit price from the server
    // For now, using placeholder value
}

/**
 * Save field value (auto-save functionality)
 */
function saveFieldValue(input) {
    const fieldName = input.name;
    const fieldValue = input.value;
    
    console.log(`Auto-saving ${fieldName}: ${fieldValue}`);
    
    // Here you would typically make an AJAX call to save the value
    // For now, just log it
}

/**
 * Debounce function to limit function calls
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showSuccess('Copiado para a área de transferência');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showSuccess('Copiado para a área de transferência');
    }
}

/**
 * Print specific element
 */
function printElement(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const printWindow = window.open('', '', 'height=600,width=800');
    printWindow.document.write('<html><head><title>Impressão</title>');
    printWindow.document.write('<link rel="stylesheet" href="/static/css/style.css">');
    printWindow.document.write('</head><body>');
    printWindow.document.write(element.outerHTML);
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    printWindow.print();
}

/**
 * Export data as CSV
 */
function exportTableAsCSV(tableId, filename = 'export.csv') {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    for (let i = 0; i < rows.length; i++) {
        const row = [];
        const cols = rows[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length; j++) {
            let data = cols[j].innerText.replace(/(\r\n|\n|\r)/gm, '').replace(/(\s\s)/gm, ' ');
            data = data.replace(/"/g, '""');
            row.push('"' + data + '"');
        }
        csv.push(row.join(','));
    }
    
    const csvFile = new Blob([csv.join('\n')], { type: 'text/csv' });
    const downloadLink = document.createElement('a');
    downloadLink.download = filename;
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

// Export functions for use in other scripts
window.BalasBaianas = {
    showError,
    showSuccess,
    formatCurrency,
    copyToClipboard,
    printElement,
    exportTableAsCSV,
    debounce
};
