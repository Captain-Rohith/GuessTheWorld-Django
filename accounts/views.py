from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect
from django.views import View
from .forms import PlayerRegistrationForm, CustomLoginForm


class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.is_admin:
                return redirect("admin_daily_report")
            return redirect("dashboard")
        form = PlayerRegistrationForm()
        return render(request, "accounts/register.html", {"form": form})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        form = PlayerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect("login")
        return render(request, "accounts/register.html", {"form": form})


class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.is_admin:
                return redirect("admin_daily_report")
            return redirect("dashboard")
        form = CustomLoginForm()
        return render(request, "accounts/login.html", {"form": form})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        form = CustomLoginForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            if user.is_admin:
                return redirect("admin_daily_report")
            return redirect("dashboard")
        return render(request, "accounts/login.html", {"form": form})


class LogoutView(View):
    def get(self, request):
        logout(request)
        messages.info(request, "You have been logged out successfully.")
        return redirect("login")

    def post(self, request):
        logout(request)
        messages.info(request, "You have been logged out successfully.")
        return redirect("login")
