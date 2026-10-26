from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse

from .models import User, Listings, WatchList, Bids, Comments


def index(request):
    return render(request, "auctions/index.html", {
        "listings": Listings.objects.all()
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

class NewItem(forms.Form):
    listing = forms.CharField(label="Item Name")
    photo = forms.FileField(label="Item Image", required= False)
    description = forms.CharField(widget=forms.Textarea, max_length=200, label="Description")
    category = forms.ChoiceField(choices=[("Other", ""), ("Fachion", "Fachion"), ("Toys", "Toys"), ("Electronics", "Electronics"), ("Home", "Home"), ("Other", "Other")], required= False)
    starting_bid = forms.FloatField(label="Staring Bid")


@login_required
def newListing(request):
    if request.method == "POST":
        form = NewItem(request.POST, request.FILES)
        if form.is_valid():
            
            listing = form.cleaned_data["listing"]

            photo = "noimage.png"
            photox = form.cleaned_data["photo"]
            if photox:
                target_dir = os.path.join(settings.BASE_DIR, 'auctions', 'static', 'uploads')
                os.makedirs(target_dir, exist_ok=True)
                fs = FileSystemStorage(location=target_dir)
                photo = fs.save(photox.name, photox)

            description = form.cleaned_data["description"]
            starting_bid = form.cleaned_data["starting_bid"]
            category = form.cleaned_data["category"]
            try: 
                item = Listings(listing= listing, photo= photo, description= description, starting_bid= starting_bid, category= category, user= request.user)
                item.save()
            except Exception: 
                return render(request, "auctions/listing.html", {
                                "message": "Must provide all required filds.",
                                "form": form
                            })
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/listing.html", {
                                            "message": "This form is not valid.",
                                            "form": form
                                        })

    else:
        return render(request, "auctions/listing.html", {
            "form": NewItem()
        })

class NewBid(forms.Form):
    bid = forms.FloatField(label="Bid")

class NewComment(forms.Form):
    comment = forms.CharField(label="Comment")    

def items(request, item):
    itemx = Listings.objects.get(id = item)
    try:    
        bidx = Bids.objects.get(listing= itemx)
    except Exception:
        bidx = False
    
    watchlist = list(WatchList.objects.values_list("listing_id", flat=True).filter(user = request.user))
    comments = Comments.objects.filter(listing= itemx)

    if request.method == "POST":
        
        act = request.POST["act"]
        if act == "Add to watchlist":
            watching = WatchList(listing= itemx, user= request.user)
            watching.save()
            return redirect("items", item= item)
        
        elif act == "Remove from watchlist":
            WatchList.objects.get(listing = itemx).delete()
            return redirect("items", item)

        elif act == "Place Bid":
            form = NewBid(request.POST)
            if form.is_valid():
                bid = form.cleaned_data["bid"]
                price = Listings.objects.get(id= item)
                pricex = price.starting_bid
                if bid >= pricex:
                    price.starting_bid = bid
                    price.save()
                    if bidx:
                        bidx.bid = bid
                        bidx.bid_number += 1
                        bidx.bidder = request.user
                        bidx.save()
                        return redirect("items", item)
                    else:
                        new_bid = Bids(bid= bid, bidder= request.user, listing= itemx)
                        new_bid.save()
                        return redirect("items", item)
                        
                else:
                    messages.error(request, "Your bid is less than the current bid")
                    return redirect("items", item)
            else:
                messages.error(request, "Your bid is not valid")
                return redirect("items", item)

        elif act == "Close auction":
            itemx.closed = True
            itemx.save()
            return redirect("items", item)
        elif act == "Add Comment":
            comment_form = NewComment(request.POST)
            if comment_form.is_valid():
                comment = comment_form.cleaned_data["comment"]
                new_comment = Comments(comment= comment, commenter= request.user, listing= itemx)
                new_comment.save()
                return redirect("items", item)
            else:
                messages.error(request, "Your comment is not valid")
                return redirect("items", item)

    else:
        return render(request, "auctions/item.html", {
            "item": itemx,
            "watchlist": watchlist,
            "form": NewBid(),
            "bid": bidx,
            "comment_form": NewComment(),
            "comments": comments,

        })

@login_required
def watchlist(request):

    return render(request, "auctions/watchlist.html", {
        "watchlist": WatchList.objects.filter(user= request.user)
    })

def categories(request):
    choices = ["Fachion", "Toys", "Electronics", "Home", "Other"]
    if request.method == "POST":
        category = request.POST["category"]
        return render(request, "auctions/categories.html", {
            "categories": choices,
            "categoryx": Listings.objects.filter(category= category)
        })
    return render(request, "auctions/categories.html", {
        "categories": choices
    })






