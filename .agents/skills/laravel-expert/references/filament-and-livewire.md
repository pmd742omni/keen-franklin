# Filament v3 & Livewire 3: Enterprise Admin Panels & Reactive Blade (2026)

> Technical reference for building high-velocity administrative control panels and full-stack reactive PHP interfaces.

---

## 1. Filament v3 Architecture

Filament is built on the TALL stack (Tailwind CSS, Alpine.js, Laravel, Livewire 3). It provides a declarative, schema-based PHP builder pattern for tables, forms, infolists, and widgets.

### 1.1 Resource Scaffolding & Declarative Forms
```php
// app/Filament/Resources/OrderResource.php
namespace App\Filament\Resources;

use App\Models\Order;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;

class OrderResource extends Resource
{
    protected static ?string $model = Order::class;
    protected static ?string $navigationIcon = 'heroicon-o-shopping-cart';

    public static function form(Form $form): Form
    {
        return $form->schema([
            Forms\Components\Section::make('Order Information')
                ->schema([
                    Forms\Components\Select::make('customer_id')
                        ->relationship('customer', 'name')
                        ->searchable()
                        ->preload()
                        ->required(),
                    Forms\Components\TextInput::make('total_amount')
                        ->numeric()
                        ->prefix('$')
                        ->required(),
                    Forms\Components\Select::make('status')
                        ->options([
                            'pending' => 'Pending',
                            'processing' => 'Processing',
                            'completed' => 'Completed',
                            'cancelled' => 'Cancelled',
                        ])
                        ->default('pending')
                        ->required(),
                ])->columns(3),
        ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('id')->searchable()->sortable(),
                Tables\Columns\TextColumn::make('customer.name')->searchable(),
                Tables\Columns\TextColumn::make('total_amount')->money('usd')->sortable(),
                Tables\Columns\BadgeColumn::make('status')
                    ->colors([
                        'warning' => 'pending',
                        'primary' => 'processing',
                        'success' => 'completed',
                        'danger' => 'cancelled',
                    ]),
                Tables\Columns\TextColumn::make('created_at')->dateTime()->sortable(),
            ])
            ->filters([
                Tables\Filters\SelectFilter::make('status')
                    ->options([
                        'pending' => 'Pending',
                        'completed' => 'Completed',
                    ]),
            ])
            ->actions([
                Tables\Actions\EditAction::make(),
                Tables\Actions\DeleteAction::make(),
            ]);
    }
}
```

---

## 2. Livewire 3: Reactive Component Architecture

Livewire components are server-rendered PHP classes that update asynchronously without requiring client-side JavaScript bundling.

### 2.1 Reactive Properties and Form Validation
```php
// app/Livewire/CreateInvoice.php
namespace App\Livewire;

use App\Models\Invoice;
use Livewire\Component;
use Livewire\Attributes\Rule;

class CreateInvoice extends Component
{
    #[Rule('required|min:3')]
    public string $clientName = '';

    #[Rule('required|numeric|min:1')]
    public float $amount = 0.0;

    public function save()
    {
        $this->validate();

        Invoice::create([
            'client_name' => $this->clientName,
            'amount' => $this->amount,
            'user_id' => auth()->id(),
        ]);

        $this->dispatch('invoice-created');
        $this->reset();
    }

    public function render()
    {
        return view('livewire.create-invoice');
    }
}
```

In the Blade template (`resources/views/livewire/create-invoice.blade.php`):
```html
<form wire:submit="save" class="space-y-4">
    <div>
        <label class="block text-sm font-medium">Client Name</label>
        <input type="text" wire:model.live.debounce.300ms="clientName" class="border rounded p-2 w-full" />
        @error('clientName') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
    </div>

    <div>
        <label class="block text-sm font-medium">Amount</label>
        <input type="number" step="0.01" wire:model="amount" class="border rounded p-2 w-full" />
        @error('amount') <span class="text-red-500 text-xs">{{ $message }}</span> @enderror
    </div>

    <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded">
        Create Invoice
    </button>
</form>
```
