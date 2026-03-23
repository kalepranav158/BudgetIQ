from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction as db_transaction
from .model import Raw_Transaction
from .parsers import process_sbi_statement, save_transaction_data
from django.conf import settings

def index(request):
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        pdf_file = request.FILES['pdf_file']
        
        try:
            raw_transactions, daily_summaries = process_sbi_statement(
                pdf_file=pdf_file,
                user=request.user if request.user.is_authenticated else None,
                filename=pdf_file.name[:100]
            )
            
            if not raw_transactions:
                messages.warning(request, "PDF uploaded but no transactions found")
                return render(request, 'smarty/index.html')
            
            with db_transaction.atomic():
                save_transaction_data(
                    raw_transactions=raw_transactions,
                    daily_summaries=daily_summaries,
                    user=request.user if request.user.is_authenticated else None,
                )
            
            messages.success(
                request,
                f"✅ Successfully processed {len(raw_transactions)} transactions from {pdf_file.name}"
            )
            return redirect('index')
            
        except ValueError as e:
            # Handle expected errors (e.g., wrong format, password protected)
            messages.error(request, f"❌ {str(e)}")
        except Exception as e:
            # Handle unexpected errors
            messages.error(
                request,
                "❌ An unexpected error occurred. Please check the file format."
            )
            if settings.DEBUG:
                print(f"Error processing PDF: {str(e)}")  # Debug output
            
        return render(request, 'smarty/index.html')
    
    # GET request or no file uploaded
    return render(request, 'smarty/index.html', {
        'recent_uploads': Raw_Transaction.objects.order_by('-created_at')[:5] if request.user.is_authenticated else None
    })