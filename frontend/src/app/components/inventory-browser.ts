// frontend/src/app/components/inventory-browser.ts
/**
 * Inventory Browser Component
 *
 * A modal/drawer component that displays available rental equipment
 * grouped by category. Allows users to browse what's available before
 * creating a quote request.
 *
 * Features:
 * - Displays equipment categories with icons and descriptions
 * - Collapsible category sections showing individual items
 * - Shows daily rates and availability for each item
 * - Loading and error states with retry functionality
 */
import { Component, EventEmitter, OnInit, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService, InventoryCategory } from '../services/api';

@Component({
  selector: 'app-inventory-browser',
  standalone: true,
  imports: [CommonModule],
  template: `
    <!-- Modal Backdrop - clicking closes the modal -->
    <div class="modal-backdrop" (click)="close()"></div>

    <!-- Modal Content -->
    <div class="modal-container">
      <!-- Header -->
      <div class="modal-header">
        <div>
          <h2 class="modal-title">What Can I Rent?</h2>
          <p class="modal-subtitle">Browse our equipment catalog by category</p>
        </div>
        <button class="btn-close" (click)="close()" aria-label="Close">&times;</button>
      </div>

      <!-- Loading State -->
      <div *ngIf="loading" class="modal-loading">
        <div class="loading-spinner-large"></div>
        <p>Loading inventory...</p>
      </div>

      <!-- Error State -->
      <div *ngIf="error && !loading" class="modal-error">
        <span class="error-icon">&#9888;</span>
        <p>{{ error }}</p>
        <button class="btn-retry" (click)="loadInventory()">Retry</button>
      </div>

      <!-- Inventory Categories -->
      <div *ngIf="!loading && !error" class="modal-body">
        <div class="category-list">
          <div *ngFor="let category of categories" class="category-card">
            <!-- Category Header (clickable to expand/collapse) -->
            <div class="category-header" (click)="toggleCategory(category.key)">
              <span class="category-icon">{{ category.icon }}</span>
              <div class="category-info">
                <h3 class="category-name">{{ category.name }}</h3>
                <p class="category-description">{{ category.description }}</p>
              </div>
              <span class="category-count">{{ category.itemCount }} items</span>
              <span class="expand-icon">{{ expandedCategories[category.key] ? '&#9660;' : '&#9654;' }}</span>
            </div>

            <!-- Category Items (Collapsible) -->
            <div *ngIf="expandedCategories[category.key]" class="category-items">
              <div *ngFor="let item of category.items" class="item-row">
                <div class="item-info">
                  <span class="item-name">{{ item.name }}</span>
                  <span class="item-sku">{{ item.sku }}</span>
                </div>
                <div class="item-pricing">
                  <span class="item-rate">\${{ item.dailyRate | number:'1.2-2' }}/day</span>
                  <span class="item-availability" [class.low-stock]="item.available < 5">
                    {{ item.available }} available
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Help Text -->
        <div class="modal-footer">
          <p class="help-text">
            <strong>Tip:</strong> Simply describe what you need in the quote form
            (e.g., "50 chairs and 5 tables for a wedding") and our AI will find the best options.
          </p>
        </div>
      </div>
    </div>
  `,
  styles: [
    `
      /* Modal Backdrop */
      .modal-backdrop {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(4px);
        z-index: 1000;
      }

      /* Modal Container */
      .modal-container {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 90%;
        max-width: 700px;
        max-height: 85vh;
        background: linear-gradient(
          145deg,
          rgba(15, 23, 42, 0.98),
          rgba(30, 41, 59, 0.95)
        );
        border-radius: 16px;
        border: 1px solid rgba(59, 130, 246, 0.3);
        box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
        z-index: 1001;
        display: flex;
        flex-direction: column;
        overflow: hidden;
      }

      /* Modal Header */
      .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        padding: 1.5rem;
        border-bottom: 1px solid rgba(59, 130, 246, 0.2);
        background: rgba(15, 23, 42, 0.5);
      }

      .modal-title {
        margin: 0;
        font-size: 1.4rem;
        font-weight: 700;
        color: #f1f5f9;
      }

      .modal-subtitle {
        margin: 0.3rem 0 0;
        font-size: 0.85rem;
        color: #94a3b8;
      }

      .btn-close {
        background: none;
        border: none;
        font-size: 1.8rem;
        color: #94a3b8;
        cursor: pointer;
        padding: 0;
        line-height: 1;
        transition: color 0.2s;
      }

      .btn-close:hover {
        color: #f1f5f9;
      }

      /* Modal Body */
      .modal-body {
        flex: 1;
        overflow-y: auto;
        padding: 1rem;
      }

      /* Loading State */
      .modal-loading {
        padding: 3rem;
        text-align: center;
        color: #94a3b8;
      }

      .loading-spinner-large {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        border: 4px solid rgba(59, 130, 246, 0.2);
        border-top-color: #60a5fa;
        animation: spin 0.8s linear infinite;
        margin: 0 auto 1rem;
      }

      @keyframes spin {
        to {
          transform: rotate(360deg);
        }
      }

      /* Error State */
      .modal-error {
        padding: 3rem;
        text-align: center;
        color: #fecaca;
      }

      .error-icon {
        font-size: 2rem;
        display: block;
        margin-bottom: 1rem;
      }

      .btn-retry {
        margin-top: 1rem;
        padding: 0.5rem 1.2rem;
        border-radius: 8px;
        border: 1px solid rgba(248, 113, 113, 0.4);
        background: rgba(248, 113, 113, 0.15);
        color: #fecaca;
        cursor: pointer;
        font-weight: 600;
      }

      .btn-retry:hover {
        background: rgba(248, 113, 113, 0.25);
      }

      /* Category List */
      .category-list {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
      }

      .category-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 12px;
        overflow: hidden;
      }

      .category-header {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        cursor: pointer;
        transition: background 0.2s;
      }

      .category-header:hover {
        background: rgba(59, 130, 246, 0.08);
      }

      .category-icon {
        font-size: 1.8rem;
      }

      .category-info {
        flex: 1;
      }

      .category-name {
        margin: 0;
        font-size: 1rem;
        font-weight: 600;
        color: #f1f5f9;
      }

      .category-description {
        margin: 0.2rem 0 0;
        font-size: 0.8rem;
        color: #94a3b8;
      }

      .category-count {
        font-size: 0.75rem;
        color: #60a5fa;
        background: rgba(59, 130, 246, 0.15);
        padding: 0.25rem 0.6rem;
        border-radius: 999px;
      }

      .expand-icon {
        color: #64748b;
        font-size: 0.8rem;
      }

      /* Category Items */
      .category-items {
        border-top: 1px solid rgba(148, 163, 184, 0.1);
        background: rgba(15, 23, 42, 0.3);
      }

      .item-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem 1rem 0.75rem 3.5rem;
        border-bottom: 1px solid rgba(148, 163, 184, 0.08);
      }

      .item-row:last-child {
        border-bottom: none;
      }

      .item-info {
        display: flex;
        flex-direction: column;
        gap: 0.15rem;
      }

      .item-name {
        font-size: 0.85rem;
        color: #e2e8f0;
      }

      .item-sku {
        font-size: 0.7rem;
        color: #64748b;
        font-family: monospace;
      }

      .item-pricing {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 0.15rem;
      }

      .item-rate {
        font-size: 0.85rem;
        color: #6ee7b7;
        font-weight: 600;
      }

      .item-availability {
        font-size: 0.7rem;
        color: #94a3b8;
      }

      .item-availability.low-stock {
        color: #fbbf24;
      }

      /* Modal Footer */
      .modal-footer {
        padding: 1rem 1.5rem;
        border-top: 1px solid rgba(59, 130, 246, 0.15);
        background: rgba(15, 23, 42, 0.5);
        margin-top: 1rem;
        border-radius: 8px;
      }

      .help-text {
        margin: 0;
        font-size: 0.8rem;
        color: #94a3b8;
        line-height: 1.5;
      }

      .help-text strong {
        color: #60a5fa;
      }

      /* Responsive */
      @media (max-width: 640px) {
        .modal-container {
          width: 95%;
          max-height: 90vh;
        }

        .category-header {
          gap: 0.75rem;
          padding: 0.85rem;
        }

        .category-icon {
          font-size: 1.5rem;
        }

        .item-row {
          padding-left: 2.5rem;
          flex-wrap: wrap;
          gap: 0.5rem;
        }

        .item-pricing {
          flex-direction: row;
          gap: 0.75rem;
        }
      }
    `,
  ],
})
export class InventoryBrowserComponent implements OnInit {
  // Output event to notify parent when modal should close
  @Output() closeModal = new EventEmitter<void>();

  // Component state
  loading = true;
  error: string | null = null;
  categories: InventoryCategory[] = [];
  expandedCategories: Record<string, boolean> = {};

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.loadInventory();
  }

  /**
   * Fetch inventory data from the API.
   * Groups equipment by category and includes pricing information.
   */
  loadInventory(): void {
    this.loading = true;
    this.error = null;

    this.api.browseInventory().subscribe({
      next: (response) => {
        this.categories = response.categories;
        // Auto-expand the first category for better UX
        if (this.categories.length > 0) {
          this.expandedCategories[this.categories[0].key] = true;
        }
        this.loading = false;
      },
      error: (err) => {
        console.error('Failed to load inventory:', err);
        this.error = 'Unable to load inventory. Please try again.';
        this.loading = false;
      },
    });
  }

  /**
   * Toggle a category's expanded/collapsed state.
   * Allows users to show/hide items within each category.
   */
  toggleCategory(key: string): void {
    this.expandedCategories[key] = !this.expandedCategories[key];
  }

  /**
   * Close the modal and emit event to parent component.
   */
  close(): void {
    this.closeModal.emit();
  }
}
