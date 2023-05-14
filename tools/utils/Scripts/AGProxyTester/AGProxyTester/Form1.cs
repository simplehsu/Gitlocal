using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Net;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace AGProxyTester
{
    public partial class Form1 : Form
    {
        // Make sure C:\temp exists.  This is a test app so it doesn't bother checking
        const string filename =  @"C:\temp\downloaded_from_aws.bin";

        public Form1()
        {
            InitializeComponent();
        }

        private void Form1_Load(object sender, EventArgs e)
        {

        }

        private void btnTest_Click(object sender, EventArgs e)
        {
            string url = tbUrl.Text;

            try
            {
                if (File.Exists(filename))
                {
                    File.Delete(filename);
                }

                var webRequest = System.Net.WebRequest.Create(url.Substring(0, url.IndexOf('?')));

                if (webRequest != null)
                {
                    webRequest.Method = "GET";
                    webRequest.Timeout = 20000;
                    webRequest.ContentType = "application/json";

                    int i = 0;
                    string headers = url.Substring(url.IndexOf('?'));
                    while (headers.Length > 0)
                    {
                        int length = Math.Min(headers.Length, 63);
                        webRequest.Headers.Add("p" + i.ToString(), headers.Substring(0, length));

                        headers = headers.Substring(length);
                        i++;
                    }

                    using (System.IO.Stream s = webRequest.GetResponse().GetResponseStream())
                    {
                        using (Stream fs = File.Create(filename))
                        {
                            s.CopyTo(fs);
                        }
                    }

                    MessageBox.Show("Firmware written to %s", filename);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("ERROR " + ex.ToString());
            }
        }

        private void btnGiant_Click(object sender, EventArgs e)
        {
            string proxy = tbProxy.Text;
            string url = tbGiantUrl.Text;

            url = System.Text.RegularExpressions.Regex.Unescape(url);

            try
            {
                if (File.Exists(filename))
                {
                    File.Delete(filename);
                }

                var webRequest = System.Net.WebRequest.Create(proxy);

                if (webRequest != null)
                {
                    webRequest.Method = "POST";
                    webRequest.Timeout = 20000;
                    webRequest.ContentType = "application/json";
                    using (var streamWriter = new StreamWriter(webRequest.GetRequestStream()))
                    {
                        streamWriter.Write(url);
                        streamWriter.Flush();
                        streamWriter.Close();
                    }

                    using (System.IO.Stream s = webRequest.GetResponse().GetResponseStream())
                    {
                        using (Stream fs = File.Create(filename))
                        {
                            s.CopyTo(fs);
                        }
                    }

                    MessageBox.Show("Firmware written to " +  filename);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("ERROR " + ex.ToString());
            }
        }

        private void btnRESTCall_Click(object sender, EventArgs e)
        {
            tbMetaData.Text = string.Empty;
            string url = "https://p.k2labs.org/api/d1/packages?sw_pkg_version=" + tbVersion.Text + "&model=" + tbModel.Text + "&host_device_type=" + tbDeviceType.Text + "&host_device_identifier=" + tbHostIdentifier.Text;

            try
            {
                var webRequest = System.Net.WebRequest.Create(url);

                if (webRequest != null)
                {
                    webRequest.Method = "GET";
                    webRequest.Timeout = 20000;
                    webRequest.ContentType = "application/json";

                    Stream objStream = webRequest.GetResponse().GetResponseStream();
                    StreamReader objReader = new StreamReader(objStream);

                    string line = string.Empty;
                    while (line != null)
                    {
                        line = objReader.ReadLine();
                        if (line != null)
                        {
                            tbMetaData.Text += System.Text.RegularExpressions.Regex.Unescape(line);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("ERROR " + ex.ToString());
            }
        }

        private void btnResolve_Click(object sender, EventArgs e)
        {
            IPHostEntry hostEntry;

            hostEntry = Dns.GetHostEntry(tbResolve.Text);

            if (hostEntry.HostName != string.Empty)
            {
                MessageBox.Show("Resolved to " + hostEntry.HostName);
            }
        }
    }
}
