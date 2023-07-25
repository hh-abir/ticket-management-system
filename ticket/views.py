from django.shortcuts import render, redirect
from django.contrib import messages
from users.models import User
from .models import Ticket
import datetime
from .form import CreateTicketForm, UpdateTicketForm
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from xhtml2pdf.default import DEFAULT_FONT

@login_required
def ticket_details(request, pk):
    ticket = Ticket.objects.get(pk=pk)
    user = User.objects.get(username = ticket.created_by)
    ticket_per_user = Ticket.objects.filter(created_by = user).order_by('-date_created')

    context = {'ticket': ticket, 'ticket_per_user': ticket_per_user}
    return render(request, 'ticket/ticket_details.html', context)

@login_required
def create_ticket(request):
    if request.method == 'POST':
        form = CreateTicketForm(request.POST)
        if form.is_valid():
            var = form.save(commit=False)
            var.created_by = request.user
            var.ticket_status = 'Pending'
            var.save()
            messages.info(request, 'Your ticket has been successfully submitted. An engineer would be assigned soon.')
            return redirect('dashboard')
        else:
            messages.warning(request, 'Something went wrong. Please check your inputs.')
            return redirect('create-ticket')
    else:
        form = CreateTicketForm()
        context = {'form': form}
        return render(request, 'ticket/create_ticket.html', context )

@login_required
def update_ticket(request, pk):
    ticket = Ticket.objects.get(pk=pk)
    if not ticket.is_resolved:
        if request.method == 'POST':
            form = UpdateTicketForm(request.POST, instance=ticket)
            if form.is_valid():
                form.save()
                messages.info(request, 'Your ticket info has been updated and all the changes has been saved in database.')
                return redirect('dashboard')
            else:
                messages.warning(request, 'Something went wrong. Please check your inputs.')
                return redirect('create-ticket')
        else:
            form = UpdateTicketForm(instance=ticket)
            context = {'form': form}
            return render(request, 'ticket/update_ticket.html', context )
    else:
        messages.warning(request, "You cannot make any changees now.")
        return redirect('dashboard')
    
@login_required
def all_tickets(request):
    tickets = Ticket.objects.filter(created_by=request.user).order_by('-date_created')
    context = {'tickets': tickets}
    return render(request, 'ticket/all_tickets.html', context)

@login_required
def ticket_queue(request):
    tickets = Ticket.objects.filter(ticket_status = 'Pending').order_by('-date_created')
    context = {'tickets': tickets}
    return render(request, 'ticket/ticket_queue.html', context)

@login_required
def accept_ticket(request, pk):
    ticket= Ticket.objects.get(pk=pk)
    ticket.assigned_to = request.user
    ticket.ticket_status = 'Active'
    ticket.accepted_date = datetime.datetime.now()
    ticket.save()
    messages.info(request, 'Ticket has been accepted. Please resolve as soon as possible.')
    return redirect('workspace')

@login_required
def close_ticket(request, pk):
    ticket= Ticket.objects.get(pk=pk)
    ticket.ticket_status = "Completed"
    ticket.is_resolved = True
    ticket.closed_date = datetime.datetime.now()
    ticket.save()
    messages.info(request, 'Ticket has been resolved. Thank you for your brilliant support (Engineer).')
    return redirect('ticket-queue')

@login_required
def workspace(request):
    tickets = Ticket.objects.filter(assigned_to= request.user, is_resolved=False)
    context = {'tickets':tickets}
    return render(request, 'ticket/workspace.html', context)

@login_required
def all_closed_tickets(request):
    tickets = Ticket.objects.filter(assigned_to = request.user, is_resolved = True)
    context = {'tickets': tickets}
    return render(request, 'ticket/all_closed_tickets.html', context)

@login_required
def delete_ticket(request, pk):
    ticket = Ticket.objects.get(pk=pk)
    ticket.delete()
    messages.warning(request, "Ticket has been deleted")
    return redirect('dashboard')

@login_required
def download_ticket(request, pk):
    ticket = Ticket.objects.get(pk=pk)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ticket {ticket.ticket_number}.pdf"'
    a4_page_size = (8.27 * 72, 11.69 * 72)
    margin = (20, 20, 40, 20)
    template = get_template('ticket_pdf.html')
    context = {"ticket":ticket}
    rendered_html = template.render(context)
    pisa_status = pisa.CreatePDF(rendered_html, dest=response, default_font=DEFAULT_FONT, pagesize=a4_page_size, margin=margin)

    # Check if PDF generation was successful, if not handle the error
    if pisa_status.err:
        return HttpResponse('PDF generation error: %s' % pisa_status.err, content_type='text/plain')
    # messages.warning(request, "Thanks for downloading your ticket")
    # return redirect('dasboard')
    return response