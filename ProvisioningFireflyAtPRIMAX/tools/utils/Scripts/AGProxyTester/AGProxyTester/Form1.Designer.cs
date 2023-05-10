namespace AGProxyTester
{
    partial class Form1
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.tbUrl = new System.Windows.Forms.TextBox();
            this.btnCustomHdr = new System.Windows.Forms.Button();
            this.btnGiant = new System.Windows.Forms.Button();
            this.tbProxy = new System.Windows.Forms.TextBox();
            this.tbGiantUrl = new System.Windows.Forms.TextBox();
            this.tbModel = new System.Windows.Forms.TextBox();
            this.tbVersion = new System.Windows.Forms.TextBox();
            this.lblPackage = new System.Windows.Forms.Label();
            this.lblVersion = new System.Windows.Forms.Label();
            this.lblHostDeviceType = new System.Windows.Forms.Label();
            this.tbDeviceType = new System.Windows.Forms.TextBox();
            this.lblHostIdentifier = new System.Windows.Forms.Label();
            this.tbHostIdentifier = new System.Windows.Forms.TextBox();
            this.btnRESTCall = new System.Windows.Forms.Button();
            this.tbMetaData = new System.Windows.Forms.TextBox();
            this.lblFotaV1 = new System.Windows.Forms.Label();
            this.lblFotaV2 = new System.Windows.Forms.Label();
            this.lblFotaV4 = new System.Windows.Forms.Label();
            this.tbResolve = new System.Windows.Forms.TextBox();
            this.btnResolve = new System.Windows.Forms.Button();
            this.SuspendLayout();
            // 
            // tbUrl
            // 
            this.tbUrl.Location = new System.Drawing.Point(27, 35);
            this.tbUrl.Name = "tbUrl";
            this.tbUrl.Size = new System.Drawing.Size(1415, 20);
            this.tbUrl.TabIndex = 0;
            // 
            // btnCustomHdr
            // 
            this.btnCustomHdr.Location = new System.Drawing.Point(27, 64);
            this.btnCustomHdr.Name = "btnCustomHdr";
            this.btnCustomHdr.Size = new System.Drawing.Size(157, 23);
            this.btnCustomHdr.TabIndex = 1;
            this.btnCustomHdr.Text = "Custom Header Test";
            this.btnCustomHdr.UseVisualStyleBackColor = true;
            this.btnCustomHdr.Click += new System.EventHandler(this.btnTest_Click);
            // 
            // btnGiant
            // 
            this.btnGiant.Location = new System.Drawing.Point(27, 193);
            this.btnGiant.Name = "btnGiant";
            this.btnGiant.Size = new System.Drawing.Size(157, 23);
            this.btnGiant.TabIndex = 2;
            this.btnGiant.Text = "Giant URL Test";
            this.btnGiant.UseVisualStyleBackColor = true;
            this.btnGiant.Click += new System.EventHandler(this.btnGiant_Click);
            // 
            // tbProxy
            // 
            this.tbProxy.Location = new System.Drawing.Point(27, 103);
            this.tbProxy.Name = "tbProxy";
            this.tbProxy.Size = new System.Drawing.Size(157, 20);
            this.tbProxy.TabIndex = 3;
            this.tbProxy.Text = "https://ag-pxy.p.k2labs.org";
            // 
            // tbGiantUrl
            // 
            this.tbGiantUrl.Location = new System.Drawing.Point(27, 159);
            this.tbGiantUrl.Name = "tbGiantUrl";
            this.tbGiantUrl.Size = new System.Drawing.Size(1415, 20);
            this.tbGiantUrl.TabIndex = 4;
            // 
            // tbModel
            // 
            this.tbModel.Location = new System.Drawing.Point(27, 286);
            this.tbModel.Name = "tbModel";
            this.tbModel.Size = new System.Drawing.Size(100, 20);
            this.tbModel.TabIndex = 5;
            this.tbModel.Text = "es-2";
            // 
            // tbVersion
            // 
            this.tbVersion.Location = new System.Drawing.Point(149, 286);
            this.tbVersion.Name = "tbVersion";
            this.tbVersion.Size = new System.Drawing.Size(100, 20);
            this.tbVersion.TabIndex = 6;
            this.tbVersion.Text = "10008";
            // 
            // lblPackage
            // 
            this.lblPackage.AutoSize = true;
            this.lblPackage.Location = new System.Drawing.Point(27, 263);
            this.lblPackage.Name = "lblPackage";
            this.lblPackage.Size = new System.Drawing.Size(50, 13);
            this.lblPackage.TabIndex = 7;
            this.lblPackage.Text = "Package";
            // 
            // lblVersion
            // 
            this.lblVersion.AutoSize = true;
            this.lblVersion.Location = new System.Drawing.Point(149, 263);
            this.lblVersion.Name = "lblVersion";
            this.lblVersion.Size = new System.Drawing.Size(42, 13);
            this.lblVersion.TabIndex = 8;
            this.lblVersion.Text = "Version";
            // 
            // lblHostDeviceType
            // 
            this.lblHostDeviceType.AutoSize = true;
            this.lblHostDeviceType.Location = new System.Drawing.Point(289, 263);
            this.lblHostDeviceType.Name = "lblHostDeviceType";
            this.lblHostDeviceType.Size = new System.Drawing.Size(93, 13);
            this.lblHostDeviceType.TabIndex = 9;
            this.lblHostDeviceType.Text = "Host Device Type";
            // 
            // tbDeviceType
            // 
            this.tbDeviceType.Location = new System.Drawing.Point(292, 285);
            this.tbDeviceType.Name = "tbDeviceType";
            this.tbDeviceType.Size = new System.Drawing.Size(100, 20);
            this.tbDeviceType.TabIndex = 10;
            this.tbDeviceType.Text = "ag";
            // 
            // lblHostIdentifier
            // 
            this.lblHostIdentifier.AutoSize = true;
            this.lblHostIdentifier.Location = new System.Drawing.Point(435, 263);
            this.lblHostIdentifier.Name = "lblHostIdentifier";
            this.lblHostIdentifier.Size = new System.Drawing.Size(72, 13);
            this.lblHostIdentifier.TabIndex = 11;
            this.lblHostIdentifier.Text = "Host Identifier";
            // 
            // tbHostIdentifier
            // 
            this.tbHostIdentifier.Location = new System.Drawing.Point(438, 285);
            this.tbHostIdentifier.Name = "tbHostIdentifier";
            this.tbHostIdentifier.Size = new System.Drawing.Size(100, 20);
            this.tbHostIdentifier.TabIndex = 12;
            this.tbHostIdentifier.Text = "ATY-GP0-FF2";
            // 
            // btnRESTCall
            // 
            this.btnRESTCall.Location = new System.Drawing.Point(27, 328);
            this.btnRESTCall.Name = "btnRESTCall";
            this.btnRESTCall.Size = new System.Drawing.Size(164, 23);
            this.btnRESTCall.TabIndex = 13;
            this.btnRESTCall.Text = "Get Package Metadata";
            this.btnRESTCall.UseVisualStyleBackColor = true;
            this.btnRESTCall.Click += new System.EventHandler(this.btnRESTCall_Click);
            // 
            // tbMetaData
            // 
            this.tbMetaData.Location = new System.Drawing.Point(209, 328);
            this.tbMetaData.Multiline = true;
            this.tbMetaData.Name = "tbMetaData";
            this.tbMetaData.Size = new System.Drawing.Size(461, 220);
            this.tbMetaData.TabIndex = 14;
            // 
            // lblFotaV1
            // 
            this.lblFotaV1.AutoSize = true;
            this.lblFotaV1.Location = new System.Drawing.Point(27, 13);
            this.lblFotaV1.Name = "lblFotaV1";
            this.lblFotaV1.Size = new System.Drawing.Size(51, 13);
            this.lblFotaV1.TabIndex = 15;
            this.lblFotaV1.Text = "FOTA V1";
            // 
            // lblFotaV2
            // 
            this.lblFotaV2.AutoSize = true;
            this.lblFotaV2.Location = new System.Drawing.Point(27, 137);
            this.lblFotaV2.Name = "lblFotaV2";
            this.lblFotaV2.Size = new System.Drawing.Size(88, 13);
            this.lblFotaV2.TabIndex = 16;
            this.lblFotaV2.Text = "FOTA V2 and V4";
            // 
            // lblFotaV4
            // 
            this.lblFotaV4.AutoSize = true;
            this.lblFotaV4.Location = new System.Drawing.Point(26, 236);
            this.lblFotaV4.Name = "lblFotaV4";
            this.lblFotaV4.Size = new System.Drawing.Size(51, 13);
            this.lblFotaV4.TabIndex = 17;
            this.lblFotaV4.Text = "FOTA V4";
            // 
            // tbResolve
            // 
            this.tbResolve.Location = new System.Drawing.Point(723, 285);
            this.tbResolve.Name = "tbResolve";
            this.tbResolve.Size = new System.Drawing.Size(133, 20);
            this.tbResolve.TabIndex = 18;
            this.tbResolve.Text = "iot.keeptruckin.com";
            // 
            // btnResolve
            // 
            this.btnResolve.Location = new System.Drawing.Point(906, 286);
            this.btnResolve.Name = "btnResolve";
            this.btnResolve.Size = new System.Drawing.Size(75, 23);
            this.btnResolve.TabIndex = 19;
            this.btnResolve.Text = "Resolve";
            this.btnResolve.UseVisualStyleBackColor = true;
            this.btnResolve.Click += new System.EventHandler(this.btnResolve_Click);
            // 
            // Form1
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(1454, 594);
            this.Controls.Add(this.btnResolve);
            this.Controls.Add(this.tbResolve);
            this.Controls.Add(this.lblFotaV4);
            this.Controls.Add(this.lblFotaV2);
            this.Controls.Add(this.lblFotaV1);
            this.Controls.Add(this.tbMetaData);
            this.Controls.Add(this.btnRESTCall);
            this.Controls.Add(this.tbHostIdentifier);
            this.Controls.Add(this.lblHostIdentifier);
            this.Controls.Add(this.tbDeviceType);
            this.Controls.Add(this.lblHostDeviceType);
            this.Controls.Add(this.lblVersion);
            this.Controls.Add(this.lblPackage);
            this.Controls.Add(this.tbVersion);
            this.Controls.Add(this.tbModel);
            this.Controls.Add(this.tbGiantUrl);
            this.Controls.Add(this.tbProxy);
            this.Controls.Add(this.btnGiant);
            this.Controls.Add(this.btnCustomHdr);
            this.Controls.Add(this.tbUrl);
            this.Name = "Form1";
            this.Text = "AG Proxy Tester";
            this.Load += new System.EventHandler(this.Form1_Load);
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion

        private System.Windows.Forms.TextBox tbUrl;
        private System.Windows.Forms.Button btnCustomHdr;
        private System.Windows.Forms.Button btnGiant;
        private System.Windows.Forms.TextBox tbProxy;
        private System.Windows.Forms.TextBox tbGiantUrl;
        private System.Windows.Forms.TextBox tbModel;
        private System.Windows.Forms.TextBox tbVersion;
        private System.Windows.Forms.Label lblPackage;
        private System.Windows.Forms.Label lblVersion;
        private System.Windows.Forms.Label lblHostDeviceType;
        private System.Windows.Forms.TextBox tbDeviceType;
        private System.Windows.Forms.Label lblHostIdentifier;
        private System.Windows.Forms.TextBox tbHostIdentifier;
        private System.Windows.Forms.Button btnRESTCall;
        private System.Windows.Forms.TextBox tbMetaData;
        private System.Windows.Forms.Label lblFotaV1;
        private System.Windows.Forms.Label lblFotaV2;
        private System.Windows.Forms.Label lblFotaV4;
        private System.Windows.Forms.TextBox tbResolve;
        private System.Windows.Forms.Button btnResolve;
    }
}
