using System;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace OCRApp.Presentation;

public sealed partial class AccountPage : Page
{
    internal AccountViewModel? VM => DataContext as AccountViewModel;

    public AccountPage()
    {
        // Workaround.
        // Generally, I think Loaded should be used instead of DataContextChanged, and the VM null check shouldn't be needed.
        this.DataContextChanged += (_, _) =>
        {
            if (VM is null)
            {
                return;
            }

            Bindings.Update();
            if (VM.LoggedInUsername is null)
            {
                VisualStateManager.GoToState(this, "Login", useTransitions: false);
            }
            else
            {
                VisualStateManager.GoToState(this, "Welcome", useTransitions: false);
            }
        };

        this.InitializeComponent();
    }

    #region Logout
    private void LogoutButton_Click(object sender, RoutedEventArgs e)
    {
        VM!.Logout();
        VisualStateManager.GoToState(this, "Login", useTransitions: false);
    }
    #endregion

    #region Signup
    private async void SignupButton_Click(object sender, RoutedEventArgs e)
    {
        if (PasswordSignupTextBox.Password != ConfirmPasswordSignupTextBox.Password)
        {
            SignupInfoBar.Message = "Password and Confirm Password fields don't match";
            SignupInfoBar.IsOpen = true;
            return;
        }

        var result = await VM!.SignupAsync(UsernameSignupTextBox.Text, PasswordSignupTextBox.Password);
        if (!result.Success)
        {
            SignupInfoBar.Message = result.Error!;
            SignupInfoBar.IsOpen = true;
            return;
        }

        var dialog = new ContentDialog()
        {
            Title = "Account created successfully",
            Content = "You can now login with your new account!",
            XamlRoot = this.XamlRoot,
            PrimaryButtonText = "Ok",
        };

        await dialog.ShowAsync();
        VisualStateManager.GoToState(this, "Login", useTransitions: false);
    }

    private void LoginHyperLink_Click(object sender, RoutedEventArgs e)
    {
        VisualStateManager.GoToState(this, "Login", useTransitions: false);
    }
    #endregion

    #region Login
    private async void LoginButton_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            LoadingControl.IsLoading = true;
            if (await VM!.LoginAsync(UsernameLoginTextBox.Text, PasswordLoginTextBox.Password))
            {
                VM.LoggedInUsername = UsernameLoginTextBox.Text;
                VisualStateManager.GoToState(this, "Welcome", useTransitions: false);
            }
            else
            {
                var dialog = new ContentDialog()
                {
                    Title = "Incorrect credentials",
                    Content = "The entered username or password is not correct.",
                    XamlRoot = this.XamlRoot,
                    PrimaryButtonText = "Ok",
                };
                await dialog.ShowAsync();
            }
        }
        catch (Exception ex)
        {
            var dialog = new ContentDialog()
            {
                Title = "Unknown error",
                Content = ex.ToString(),
                XamlRoot = this.XamlRoot,
                PrimaryButtonText = "Ok",
            };
            await dialog.ShowAsync();
        }
        finally
        {
            LoadingControl.IsLoading = false;
        }
    }

    private void SignupHyperlink_Click(object sender, RoutedEventArgs e)
    {
        VisualStateManager.GoToState(this, "Signup", useTransitions: false);
    }
    #endregion
}
