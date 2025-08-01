# src/api/finance.py - Fixed routes with proper separation

from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from src.finance import SimpleFinanceService, get_finances
from src.utils import owner_required, getUser, lang

finance_blueprint = Blueprint('finance', __name__, url_prefix='/admin')

@finance_blueprint.route("/finances")
@owner_required
def finances():
    """Main finances dashboard with CHART - your original dashboard"""
    try:
        (
            labels,
            revenue_data_points,
            hosting_spending_data_points,
            translation_spending_data_points,
            api_subscription_spending_data_points,
            api_topup_spending_data_points,
            total_spending_data_points,
            profit_data_points,
            totals,
        ) = get_finances()
        
        return render_template(
            "admin/finances.html",  # This should be your ORIGINAL chart template
            labels=labels,
            revenue_data_points=revenue_data_points,
            hosting_spending_data_points=hosting_spending_data_points,
            translation_spending_data_points=translation_spending_data_points,
            api_subscription_spending_data_points=api_subscription_spending_data_points,
            api_topup_spending_data_points=api_topup_spending_data_points,
            total_spending_data_points=total_spending_data_points,
            profit_data_points=profit_data_points,
            totals=totals,
            username=getUser(),
            title="Finances",
            **lang[session["userinfo"]["lang"]],
            **session["userinfo"],
        )
    except Exception as e:
        flash(f"Error loading financial data: {str(e)}", "error")
        return render_template("admin/error.html", error=str(e))

@finance_blueprint.route("/finances/manage")
@owner_required
def manage():
    """Simple finance management page - separate from dashboard"""
    try:
        expenses = SimpleFinanceService.get_all_expenses()
        revenues = SimpleFinanceService.get_all_revenue()
        
        # Separate recurring and one-time expenses
        recurring_expenses = [e for e in expenses if e['is_recurring']]
        one_time_expenses = [e for e in expenses if not e['is_recurring']]
        
        return render_template(
            "admin/manage_finances.html",  # This should be your management template
            recurring_expenses=recurring_expenses,
            one_time_expenses=one_time_expenses,
            revenues=revenues,
            username=getUser(),
            title="Manage Finances",
            **lang[session["userinfo"]["lang"]],
            **session["userinfo"],
        )
    except Exception as e:
        flash(f"Error loading management page: {str(e)}", "error")
        return render_template("admin/error.html", error=str(e))

@finance_blueprint.route("/finances/add-recurring", methods=["POST"])
@owner_required
def add_recurring():
    """Add recurring expense"""
    try:
        name = request.form.get("name", "").strip()
        amount = float(request.form.get("amount"))
        currency = request.form.get("currency", "EUR")
        start_date = datetime.strptime(request.form.get("start_date"), "%Y-%m-%d").date()
        end_date = None
        if request.form.get("end_date"):
            end_date = datetime.strptime(request.form.get("end_date"), "%Y-%m-%d").date()
        
        if not name or amount <= 0:
            flash("Name and positive amount required", "error")
            return redirect(url_for("finance.manage"))
        
        expense_id = SimpleFinanceService.add_recurring_expense(name, amount, currency, start_date, end_date)
        flash(f"Added recurring expense: {name} (#{expense_id})", "success")
        
    except Exception as e:
        flash(f"Error adding expense: {str(e)}", "error")
    
    return redirect(url_for("finance.manage"))

@finance_blueprint.route("/finances/add-onetime", methods=["POST"])
@owner_required
def add_onetime():
    """Add one-time expense"""
    try:
        name = request.form.get("name", "").strip()
        amount = float(request.form.get("amount"))
        currency = request.form.get("currency", "EUR")
        expense_date = datetime.strptime(request.form.get("expense_date"), "%Y-%m-%d").date()
        
        if not name or amount <= 0:
            flash("Name and positive amount required", "error")
            return redirect(url_for("finance.manage"))
        
        expense_id = SimpleFinanceService.add_one_time_expense(name, amount, currency, expense_date)
        flash(f"Added one-time expense: {name} (#{expense_id})", "success")
        
    except Exception as e:
        flash(f"Error adding expense: {str(e)}", "error")
    
    return redirect(url_for("finance.manage"))

@finance_blueprint.route("/finances/add-revenue", methods=["POST"])
@owner_required
def add_revenue():
    """Add revenue entry"""
    try:
        name = request.form.get("name", "").strip()
        amount = float(request.form.get("amount"))
        currency = request.form.get("currency", "EUR")
        revenue_date = datetime.strptime(request.form.get("revenue_date"), "%Y-%m-%d").date()
        
        if not name or amount <= 0:
            flash("Name and positive amount required", "error")
            return redirect(url_for("finance.manage"))
        
        revenue_id = SimpleFinanceService.add_revenue(name, amount, currency, revenue_date)
        flash(f"Added revenue: {name} (#{revenue_id})", "success")
        
    except Exception as e:
        flash(f"Error adding revenue: {str(e)}", "error")
    
    return redirect(url_for("finance.manage"))

@finance_blueprint.route("/finances/toggle/<int:expense_id>", methods=["POST"])
@owner_required
def toggle_expense(expense_id):
    """Toggle recurring expense active status"""
    try:
        result = SimpleFinanceService.toggle_recurring_expense(expense_id)
        if result:
            status = "activated" if result['is_active'] else "deactivated"
            flash(f"Expense '{result['name']}' {status}", "success")
        else:
            flash("Expense not found or not recurring", "error")
    except Exception as e:
        flash(f"Error toggling expense: {str(e)}", "error")
    
    return redirect(url_for("finance.manage"))

@finance_blueprint.route("/finances/delete-expense/<int:expense_id>", methods=["POST"])
@owner_required
def delete_expense(expense_id):
    """Delete expense"""
    try:
        name = SimpleFinanceService.delete_expense(expense_id)
        if name:
            flash(f"Deleted expense: {name}", "success")
        else:
            flash("Expense not found", "error")
    except Exception as e:
        flash(f"Error deleting expense: {str(e)}", "error")
    
    return redirect(url_for("finance.manage"))

@finance_blueprint.route("/finances/delete-revenue/<int:revenue_id>", methods=["POST"])
@owner_required
def delete_revenue(revenue_id):
    """Delete revenue"""
    try:
        name = SimpleFinanceService.delete_revenue(revenue_id)
        if name:
            flash(f"Deleted revenue: {name}", "success")
        else:
            flash("Revenue not found", "error")
    except Exception as e:
        flash(f"Error deleting revenue: {str(e)}", "error")
    
    return redirect(url_for("finance.manage"))

@finance_blueprint.route("/finances/sync-stripe", methods=["POST"])
@owner_required
def sync_stripe():
    """Sync Buy Me a Coffee data with duplicate prevention and amount tracking"""
    try:
        result = SimpleFinanceService.sync_stripe_revenue()
        
        if "error" in result:
            flash(f"Stripe sync error: {result['error']}", "error")
        else:
            message_parts = []
            if result["added"] > 0:
                amount_str = f" ({result.get('total_amount_added', 0):.2f}€)" if 'total_amount_added' in result else ""
                message_parts.append(f"Added {result['added']} new entries{amount_str}")
            if result["skipped"] > 0:
                message_parts.append(f"{result['skipped']} already imported")
            
            if result["added"] == 0 and result["skipped"] == 0:
                flash("No Stripe data found to sync", "warning")
            else:
                total_msg = f" (Total fetched: {result['total_fetched']})"
                flash(f"Stripe sync completed: {', '.join(message_parts)}{total_msg}", "success")
        
    except Exception as e:
        flash(f"Error syncing Stripe data: {str(e)}", "error")
    
    return redirect(url_for("finance.manage"))