;;; tmda.el -- routines for integrating TMDA with Gnus and Message mode
;; Copyright (C) 2002 Josh Huber <huber@alum.wpi.edu>

;; This program is free software; you can redistribute it and/or modify
;; it under the terms of the GNU General Public License as published by
;; the Free Software Foundation; either version 2 of the License, or
;; (at your option) any later version.

;; This program is distributed in the hope that it will be useful,   
;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;; GNU General Public License for more details.

;; You should have received a copy of the GNU General Public License
;; along with this program; if not, write to the Free Software
;; Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

;; About tmda.el
;;
;; This module contains useful helper routines for using TMDA from
;; Gnus (and perhaps other Emacs based mail/news readers).  Read on to
;; learn how to install and use tmda.el.  If you have any feedback
;; and/or bugreports (even feature requests), please email them to
;; me. (huber@alum.wpi.edu)

;; Installation instructions:
;;
;; 0. Make sure all the TMDA utilities are in your path.
;;
;; 1. Copy tmda.el somewhere in your load-path
;;
;; 2. Add the following two lines to your Gnus startup file (typically
;;    ~/.gnus or ~/.gnus.el
;;
;;    (require 'tmda)
;;    (tmda-install-hooks)
;;
;; 3. Optionally, add any combination of these to really take
;;    advantage of TMDA and tmda.el
;;
;;    (add-hook 'bbdb-change-hook 'tmda-bbdb-to-whitelist)
;;    (setq bbdb-canonicalize-net-hook 'tmda-normalize-address)
;;    (setq sendmail-program "tmda-sendmail")
;;
;; 4. Possibily configure any of the following tmda.el variables
;;
;;    tmda-bbdb-whitelist-file
;;    tmda-list-append-confirm
;;    tmda-wildcard-list-append-confirm
;;    tmda-default-whitelist
;;    tmda-default-blacklist
;;    tmda-default-wildcard-whitelist
;;    tmda-default-wildcard-blacklist
;;    tmda-pending-tag-auto-advance
;;    tmda-pending-summary-args
;;    tmda-pending-truncate-lines
;;
;;    See the help text for each variable for more information.
;;
;; 5. Display the number of pending messages in your modeline
;;
;;    Optionally, you can make use of the tmda-pending-update-count
;;    function to display the current number of pending messages in
;;    your modeline.  You will need to customize a couple things
;;    to get this to work.
;;
;;    a. You must add (list "" 'tmda-pending-count) to the
;;       default-modeline-format.  This format ensures the value
;;       can be updated dynamically.
;;
;;    b. You must arrange to have tmda-pending-update-count called
;;       every so often.  I recommend using the gnus-demon:
;;
;;       (gnus-demon-add-handler 'tmda-pending-update-count 2 t)
;;
;;    After these changes, my modeline looks like:
;;
;; ISO8-P23---**- L74 C2 XEmacs: tmda.el 11:40am 0.01 (Emacs-Lisp Font)-8%
;;      ^^^ pending count here

;; Usage Instructions

;; Installing the tmda-hooks (tmda-install-hooks) adds several
;; keybindings to various parts of Gnus and message mode.  Several
;; keybindings are also added to the global keymap.

;;    Global keybindings

;;    tmda-generate-address
;;    C-c M-t a
;;
;;    Prompt for dated, sender or keyword address in X-TMDA format and
;;    display a newly generated address in the mini-buffer.  This also
;;    copies the newly generated address to the kill-ring.

;;    tmda-whitelist-at-point, tmda-whitelist-wildcard-at-point
;;    tmda-summary-whitelist-sender, tmda-summary-whitelist-wildcard-sender
;;    C-c M-t w
;;    C-c M-t W
;;
;;    Add the address at point to the whitelist.  The capitalized
;;    version (W) adds a wildcarded version to the whitelist.  The
;;    wildcard version strips off the extention part of the address at
;;    point and replaces it with *.  When in the summary buffer, these
;;    keybindings whitelist the sender address instead.

;;    tmda-blacklist-at-point, tmda-blacklist-wildcard-at-point
;;    tmda-summary-blacklist-sender, tmda-summary-blacklist-wildcard-sender
;;    C-c M-t b
;;    C-c M-t B
;;
;;    Add the address at point to the blacklist.  The capitalized
;;    version (W) adds a wildcarded version to the blacklist.  The
;;    wildcard version strips off the extention part of the address at
;;    point and replaces it with *.  When in the summary buffer, these
;;    keybindings blacklist the sender address instead.

;;    tmda-pending
;;    C-c M-t p
;;
;;    Enters an interactive mode for viewing the tmda-pending queue.
;;    The usage should be fairly straightforward.  If you would like a
;;    different output method for tmda-pending, please customize
;;    tmda-pending-summary-args. (For example, to get a more terse
;;    output set said variable to "-bT")  If you customize your
;;    tmda-pending output, you *must* include the msg filename, as this
;;    is what the tmda-pending buffer uses to distinguish messages.

;;    Message mode keybindings
;;    These bindings are in addition to the existing global bindings

;;    tmda-generate-header
;;    C-c C-f T
;;
;;    Assists in generation of the X-TMDA header with tab completion.
;;    Sender style headers autocomplete to the current list of
;;    recipients in the message buffer.

;;    tmda-check-recipient-status
;;    C-c M-t s
;;
;;    Shows a buffer contating the actions TMDA will take on each
;;    address while sending.  From within this buffer you can
;;    whitelist or blacklist any recipient.

;;    Enjoy!

;; Version history:

;; 11/06/2002 v0.11
;;  * Reorganized the changelist structure to be more efficient
;;  * Made the "fit-to-window" code a little better.

;; 7/31/2002 v0.10
;;  * Fixed regexp for addr-at-point routine
;;  * Changed display of tmda-pending to better show new messages
;;  * Changed tmda-pending default to terse output
;;  * Fixed a few bugs in tmda-pending
;;  * Added tmda-pending-truncate-lines and support code

;; 7/26/2002 - v0.9
;;  * Made the address at point matching a little better.
;;  * Fixed a regexp in the tmda-pending mode for removing a blank line.
;;  * added tmda-pending-count for display in modeline (see installation #5)

;; 7/24/2002 - v0.8
;;  * Added keybindings to add addresses to wildcard lists
;;  * Changed tmda-no-confirmations to tmda-(wildcard-?)list-append-confirm
;;  * Several small bug fixes and reorgs of code
;;  * Added usage instructions

;; 7/24/2002 - v0.7
;;  * Made tmda-install-hooks be less intrusive.
;;  * Added more installation text
;;  * Fixed (another) bug in the summary view. (now it really works!)

;; 7/23/2002 - v0.6
;;  * Fixed more bugs in tmda-pending when the output is terse (-T)
;;  * tmda-addr-at-point is better now
;;  * Fixed major bug in the recipient summary view (it works now!)

;; 7/23/2002 - v0.5
;;  * Fixed several bugs in tmda-pending mode wrt building the changelist

;; 7/23/2002 - v0.4
;;  * Added the tmda-pending mode
;;  * Added a check for the TMDA version
;;  * Fixed a couple bugs in the summary view
;;  * Bound require-final-newline during save
;;  * Added tmda-no-confirmations variable

;; 7/22/2002 - v0.3
;;  * Fixed some (obvious, oops!) bugs with the summary output routines
;;  * Added tmda-generate-address, an interface to tmda-address
;;  * Added bare and bare=append to the completion table (header gen)

;; 7/21/2002 - v0.2
;;  * Added support for generating the X-TMDA header
;;  * Removed replace-in-string since Emacs doesn't have it.
;;  * Added a couple requires.

;; 7/20/2002 - initial release v0.1

(require 'gnus)
(require 'message)

;;; Variables

(defvar tmda-version
  "tmda.el v0.9")

(defvar tmda-bbdb-whitelist-file
  "~/.tmda/lists/bbdb-whitelist"
  "*Specifies the output file to update when a bbdb change is made.")

(defvar tmda-command-output-sep
  "^-+$"
  "Separator between sections of output from tmda-inject and tmda-filter.")

(defvar tmda-command-output-failmsg
  "Sorry, no matching lines."
  "Text output by tmda-inject/filter when no match is found.")

(defvar tmda-list-append-confirm
  t
  "*When set to t, ask for confirmation before updating a list.")

(defvar tmda-wildcard-list-append-confirm
  t
  "*When set to t, ask for confirmation before updating a wildcard list.")

(defvar tmda-output-buffer
  " *tmda-output*"
  "Buffer name to use for status display.")

(defvar tmda-pending-buffer
  " *tmda-pending*"
  "Buffer name to use for interactive pending management.")

(defvar tmda-pending-show-buffer
  " *tmda-pending-show*"
  "Buffer used to display messages in the pending queue.")

(defvar tmda-output-help-text
  "Keybindings available in this buffer:
q        kill buffer (quit)
w        whitelist address at point
b        blacklist address at point")

(defvar tmda-pending-help-text
  "Keybindings available in this buffer:
q        kill buffer (quit)
s        show
r        release
d        delete
c/SPC    clear mark
x        apply changes
n        next message
p        previous message
C-r      refresh buffer")

(defvar tmda-default-whitelist
  (concat (getenv "HOME") "/.tmda/lists/whitelist")
  "*Location of the default whitelist used by the
tmda-whitelist-at-point function.")

(defvar tmda-default-wildcard-whitelist
  "~/.tmda/lists/whitelist"
  "*Specifies a whitelist for adding wildcard entries to.  This file
must *not* be database indexed (using dbm or cdb, etc).")

(defvar tmda-default-blacklist
  (concat (getenv "HOME") "/.tmda/lists/blacklist")
  "*Location of the default blacklist used by the
tmda-blacklist-at-point function.")

(defvar tmda-default-wildcard-blacklist
  "~/.tmda/lists/blacklist"
  "*Specifies a blacklist for adding wildcard entries to.  This file
must *not* be database indexed (using dbm or cdb, etc).")

(defvar tmda-header-comp-table
  '(("keyword=")
    ("dated")
    ("dated=")
    ("sender=")
    ("bare")
    ("bare=append")
    ("ext=")
    ("exp="))
  "List of possible completions for the X-TMDA header.")

(defvar tmda-pending-act-cmd-alist
  '((?r . "-r")
    (?d . "-d")))

(defvar tmda-pending-tag-auto-advance t
  "*Advance to the next message on a tag action if non-nil.")

;;; Functions

(defun tmda-bbdb-to-whitelist (&optional junk)
  (interactive)
  (let ((records (bbdb-records))
	(file (expand-file-name tmda-bbdb-whitelist-file)))
    (with-temp-buffer
      (erase-buffer)
      ;; loop over each record
      (dolist (rec records)
	;; loop over each email address
	(dolist (addr (bbdb-record-net rec))
	    ;; ...and insert it into the whitelist
	    (insert (concat addr "\n")))
	;; don't forget the mail-alias record
	(let ((mail-alias (bbdb-record-getprop rec 'mail-alias)))
	    (when mail-alias
	          (insert (concat mail-alias "\n")))))
      ;; Now, convert all the ", " => "\n" from mail-alias
      (goto-char (point-min))
      (while (search-forward ", " nil t)
	(replace-match "\n" nil t))
      (write-file file)
      (kill-buffer (current-buffer)))))

(defun tmda-normalize-address (addr)
  "Strip the extention off an address which is passed in.
This handles the case of both + and - style extention addressing."
  (when addr
    (cond ((string-match
	    "\\`\\(.*?\\)\\(?:[+-][^@]*\\)\\(@.*\\)\\'" addr)
	   (concat (match-string 1 addr) (match-string 2 addr)))
	  (t addr))))

(defun tmda-make-dated-address ()
  "Generate a dated address with the tmda-address utility.
This can be useful in posting-styles:

(setq posting-styles
      '((\".*\"
	 (name \"Your Name\")
	 (address \"default@foo.bar.com\"))
	((message-news-p)
	 (address tmda-dated-address))))"
  (shell-command-to-string "tmda-address -d -n"))

(defun tmda-check-status (program to from)
  (with-temp-buffer
    (insert (shell-command-to-string
	     (concat program " -M " to " " from)))
    (save-excursion
      (goto-char (point-min))
      (when (search-forward tmda-command-output-failmsg nil t)
	(replace-match
	 "No match found, using default outgoing action.")))
    (goto-char (point-max))
    (if (re-search-backward tmda-command-output-sep nil t)
	(let ((text (buffer-substring (1+ (match-end 0))
				     (1- (point-max)))))
	  (concat "<= " to "\n=> " text))
      (message
       "Invalid output from tmda-inject: check TMDA installation."))))

(defun tmda-output-buffer-kill ()
  (interactive)
  (kill-buffer tmda-output-buffer))

(defun tmda-addr-at-point ()
  (save-excursion
    (let* ((mstr "=A-Za-z0-9_\\.\\+\\-")
	   (not-match-regexp (format "\\(\\`\\|[^@%s]\\)" mstr))
	   (addr-regexp (format "\\([%s]*@[%s]*\\)" mstr mstr)))
      (re-search-backward not-match-regexp nil t)
      (if (re-search-forward addr-regexp nil t)
	  (match-string 1)
	""))))

(defun tmda-summary-sender ()
  (save-excursion
    (gnus-summary-select-article)
    (set-buffer (get-buffer gnus-original-article-buffer))
    (mail-strip-quoted-names
     (mail-fetch-field "From"))))

(defun tmda-wildcard (addr)
  "Takes an address and generates a match rule which is more generic.
This is useful for whitelisting someone who is using a dated address."
  (if (string-match "\\`\\(.*?\\)\\(?:[+-][^@]*\\)?@\\(.*\\)\\'" addr)
      (concat (match-string 1 addr) "*@" (match-string 2 addr))))

;; Ease the creation of all these functions!
(defmacro tmda-make-list-function (name str addrform addrlist confirm
					&optional help)
  `(defun ,name (&optional dontask)
     ,help
     (interactive "P")
     (let ((addr ,addrform))
       (if (or dontask (not ,confirm)
	       (setq addr
		     (completing-read (concat "Address to " ,str ": ")
				      nil nil nil addr)))
	   (tmda-add-to-list addr ,addrlist))
       (message nil))))

;; The suite of black/whitelisting functions

;; whitelists
(tmda-make-list-function tmda-whitelist-at-point
			 "whitelist" (tmda-addr-at-point)
			 tmda-default-whitelist
			 tmda-list-append-confirm
			 "Whitelist address at point.")

(tmda-make-list-function tmda-summary-whitelist-sender
			 "whitelist" (tmda-summary-sender)
			 tmda-default-whitelist
			 tmda-list-append-confirm
			 "Whitelist sender in summary mode.")

(tmda-make-list-function tmda-whitelist-wildcard-at-point
			 "wildcard whitelist" (tmda-wildcard
					       (tmda-addr-at-point))
			 tmda-default-wildcard-whitelist
			 tmda-wildcard-list-append-confirm
			 "Whitelist address wildcard at point.")

(tmda-make-list-function tmda-summary-whitelist-wildcard-sender
			 "wildcard whitelist" (tmda-wildcard
					       (tmda-summary-sender))
			 tmda-default-wildcard-whitelist
			 tmda-wildcard-list-append-confirm
			 "Whitelist sender wildcard in summary buffer.")

;; blacklists
(tmda-make-list-function tmda-blacklist-at-point
			 "blacklist" (tmda-addr-at-point)
			 tmda-default-blacklist
			 tmda-list-append-confirm
			 "Blacklist address at point.")

(tmda-make-list-function tmda-summary-blacklist-sender
			 "blacklist" (tmda-summary-sender)
			 tmda-default-blacklist
			 tmda-list-append-confirm
			 "Blacklist sender in summary mode.")

(tmda-make-list-function tmda-blacklist-wildcard-at-point
			 "wildcard blacklist" (tmda-wildcard
					       (tmda-addr-at-point))
			 tmda-default-wildcard-blacklist
			 tmda-wildcard-list-append-confirm
			 "Blacklist address wildcard at point.")

(tmda-make-list-function tmda-summary-blacklist-wildcard-sender
			 "wildcard blacklist" (tmda-wildcard
					       (tmda-summary-sender))
			 tmda-default-wildcard-blacklist
			 tmda-wildcard-list-append-confirm
			 "Blacklist sender wildcard in summary buffer.")

(defun tmda-add-to-list (addr file)
  (message "Adding to %s ..." file)
  (let ((require-final-newline t))
    (with-temp-buffer
      (insert-file-contents-literally file)
      (goto-char (point-min))
      (if (re-search-forward
	   (concat "^" (regexp-quote addr) "$") nil t)
	  (message "%s already in %s" addr file)
	(goto-char (point-max))
	(insert addr)
	(write-file file)))))

(defun tmda-check-recipient-status ()
  (interactive)
  (save-restriction
    (save-excursion
      (message-options-set-recipient)))
  (let* ((recipients (message-tokenize-header
		      (gnus-strip-whitespace
		       (message-options-get 'message-recipients))))
	 (from (or (message-options-get 'message-sender)
		   user-mail-address))
	 (tmda-header (message-fetch-field "X-TMDA")))
    (switch-to-buffer tmda-output-buffer t)
    ;; setup keybindings
    (local-set-key "q" 'tmda-output-buffer-kill)
    (local-set-key "w" 'tmda-whitelist-at-point)
    (local-set-key "b" 'tmda-blacklist-at-point)
    (insert (mapconcat
	     '(lambda (addr)
		(tmda-check-status "tmda-inject" addr from))
	     recipients "\n"))
    (when tmda-header
      (insert (concat "\n\nNote, actions are overriden by X-TMDA header: "
		      tmda-header)))
    (insert (concat "\n\n" tmda-output-help-text))
    (toggle-read-only))
  (goto-char (+ 3 (point-min))))

(defun tmda-header-completion-function (str pred type)
  ;; special cases first
  (let (tstr completion-table)
    (cond ((string-match "^sender=" str)
	   ;; show completions as all the message recipients
	   (save-restriction
	     (save-excursion
	       (when (boundp 'tmda-original-msg-buf)
		 (set-buffer tmda-original-msg-buf))
	       (message-options-set-recipient)
	       (let* ((recipients (message-tokenize-header
				   (gnus-strip-whitespace
				    (message-options-get 'message-recipients))))
		      (from (message-options-get 'message-sender)))
		 (setq completion-table
		       (mapcar
			'(lambda (recipient)
			   (list (concat "sender=" recipient)))
			recipients))))))
	  (t
	   (setq completion-table tmda-header-comp-table)))
    (cond
     ((eq type nil)
      (try-completion str completion-table pred))
     ((eq type t)
      (all-completions str completion-table pred))
     ((eq type 'lambda)
      (when (try-completion str completion-table pred)
	t)))))

(defun tmda-generate-header ()
  "Add an X-TMDA header interactively in message mode."
  (interactive)
  (save-excursion
    (message-remove-header "X-TMDA")
    (let* ((tmda-original-msg-buf (current-buffer))
	   (header (completing-read "X-TMDA header: "
				   'tmda-header-completion-function)))
      (when (not (string= header ""))
	(message-position-on-field "X-TMDA" "From")
	(insert header)))))

(defun tmda-generate-address (&optional override-address)
  "Turns a string in the same format as the X-TMDA header into
a TMDA address with the tmda-address utility.  Specify a prefix
argument to override the default address.

The generated address is displayed in the minibuffer and added
to the kill ring for easy pasting wherever it is needed."
  (interactive "P")
  (let* ((header (completing-read "X-TMDA header: "
				 '(("keyword=") ("sender=")
				   ("dated") ("dated="))))
	 (addropt
	  (if override-address
	      (concat " -a" (completing-read "Address: " nil)) ""))
	 (string
	  (cond ((string-match "\\`dated=?\\(.*\\)?\\'" header)
		 (let ((timeout (match-string 1 header)))
		   (shell-command-to-string
		    (concat "tmda-address -n -d " (if timeout timeout "")
			    addropt))))
		((string-match "\\`keyword=\\(.+\\)\\'" header)
		 (let ((keyword (match-string 1 header)))
		   (shell-command-to-string
		    (concat "tmda-address -n -k " keyword addropt))))
		((string-match "\\`sender=\\(.+\\)\\'" header)
		 (let ((sndr (match-string 1 header)))
		   (shell-command-to-string
		    (concat "tmda-address -n -s " sndr addropt))))
		(t
		 nil))))
    (if string
	(progn
	  (message "%s" string)
	  (kill-new string))
      (message "Invalid syntax, please try again."))))

;;; tmda-pending buffer support code

(defun tmda-pending-buffer-kill ()
  (interactive)
  (let* ((changes (tmda-pending-changelist))
	 (quit (if (or (cdr (assoc ?d changes))
		       (cdr (assoc ?r changes)))
		   (y-or-n-p
		    "Quit tmda-pending buffer without applying changes? ")
		   t)))
    (when quit
      (kill-buffer tmda-pending-buffer))))

(defun tmda-pending-show-buffer-kill ()
  (interactive)
  (kill-buffer tmda-pending-show-buffer)
  (switch-to-buffer tmda-pending-buffer t))

(defvar tmda-pending-summary-args
  "-bT"
  "*Arguments to pass to tmda-pending to generate a summary.")

(defvar tmda-pending-truncate-lines t
  "*If value is t, truncate lines in the tmda-pending buffer to the
current window size.")

(defun tmda-pending-refresh-buffer ()
  (interactive)
  (switch-to-buffer tmda-pending-buffer t)
  (toggle-read-only 0)
  (erase-buffer)
  (insert "-*- New pending messages -*-\n\n")
  (insert (shell-command-to-string
	   (concat "tmda-pending -C " tmda-pending-summary-args)))
  (insert "\n-*- Complete list of pending messages -*-\n\n")
  (insert (shell-command-to-string
	   (concat "tmda-pending " tmda-pending-summary-args)))
  ;; put tag placeholders at the start of lines with msgids
  (save-excursion
    (let ((winwidth (1- (window-width))))
      (goto-char (point-min))
      (while (not (eobp))
        (cond ((looking-at ".*[0-9.]+\\.msg[\t ]")
               (insert "[ ] "))
              ((looking-at "^$"))      ; do nothing
              ((looking-at "^-\\*- ")) ; again, do nothing
              (t
               (insert "    ")))
        (when tmda-pending-truncate-lines
          (let ((curwidth (save-excursion (end-of-line) (current-column))))
            (when (> curwidth winwidth)
              (save-excursion
                (move-to-column winwidth)
                (kill-line)))))
        (forward-line))))
  (insert (concat "\n" tmda-pending-help-text))
  (goto-char (point-min))
  (tmda-pending-next-msg)
  (toggle-read-only 1))

(defun tmda-pending-msg ()
  (save-excursion
    (beginning-of-line)
    (when (looking-at "\\[.\\] ")
      (progn (re-search-forward "\\([0-9.]+msg\\)[\t ]")
	     (match-string 1)))))

(defmacro tmda-pending-command (&rest forms)
  "Make the tmda-pending commands a little easier to read."
  `(let ((msg (tmda-pending-msg)))
     (if msg
	 (progn
	   ,@forms)
       (message "Not a message line"))))

(defun tmda-pending-show ()
  (interactive)
  (tmda-pending-command
   (switch-to-buffer tmda-pending-show-buffer t)
   (toggle-read-only 0)
   (erase-buffer)
   (insert (shell-command-to-string
	    (concat "tmda-pending -qbS " msg)))
   (local-set-key "q" 'tmda-pending-show-buffer-kill)
   (goto-char (point-min))
   (toggle-read-only 1)))

(defun tmda-pending-tag-command (char)
  (tmda-pending-command
   (save-excursion
     (beginning-of-line)
     (forward-char)
     (toggle-read-only 0)
     (delete-char 1)
     (insert char)
     (toggle-read-only 1))
   (when tmda-pending-tag-auto-advance
     (tmda-pending-next-msg))))

(defun tmda-pending-delete ()
  (interactive)
  (tmda-pending-tag-command "d"))

(defun tmda-pending-release ()
  (interactive)
  (tmda-pending-tag-command "r"))

(defun tmda-pending-clear-mark ()
  (interactive)
  (tmda-pending-tag-command " "))

(defun tmda-pending-backward-clear ()
  "Clear any tagged operation on the previous line."
  (interactive)
  (let ((tmda-pending-tag-auto-advance nil))
    (if (tmda-pending-prev-msg)
	(tmda-pending-tag-command " ")
	(error "No previous message."))))

(defun tmda-pending-changelist ()
  (save-excursion
    (goto-char (point-min))
    (let (msg
          (first t)
          (changelist (mapcar (function list) '(?d ?r))))
      (while (or first (tmda-pending-next-msg))
	(when (setq msg (tmda-pending-msg))
	  (let* ((tag (char-after (1+ (point))))
		 (cell (assoc tag changelist)))
	    (if cell
		(setcdr cell (cons msg (cdr cell))))))
	(setq first nil))
      changelist)))

(defun tmda-pending-apply-changes ()
  (interactive)
  (let* ((changes (tmda-pending-changelist))
         (dels (cdr (assoc ?d changes)))
         (rels (cdr (assoc ?r changes))))
    (message "Processing...")
    (when (< 0 (length dels))
      (message "Processing...deletes")
      (message "%s" (shell-command-to-string
		     (format "tmda-pending -b -d %s"
			     (mapconcat 'identity dels " ")))))
    (when (< 0 (length rels))
      (message "Processing...releases")
      (message "%s" (shell-command-to-string
		     (format "tmda-pending -b -r %s"
			     (mapconcat 'identity rels " "))))))
  (sleep-for 0.5)
  (message "Processing...refreshing pending list")
  (tmda-pending-refresh-buffer)
  (tmda-pending-update-count)
  (message "Processing...done."))

(defun tmda-pending-next-msg ()
  (interactive)
  (let ((cur (point)))
    (forward-char)
    (re-search-forward "^\\[.\\]" nil t)
    (beginning-of-line)
    (not (= cur (point)))))

(defun tmda-pending-prev-msg ()
  (interactive)
  (let ((cur (point)))
    (beginning-of-line)
    (re-search-backward "^\\[.\\]" nil t)
    (not (= cur (point)))))

(defun tmda-pending-setup-keys ()
  (local-set-key "q" 'tmda-pending-buffer-kill)
  (local-set-key "s" 'tmda-pending-show)
  (local-set-key (kbd "RET") 'tmda-pending-show)
  (local-set-key "r" 'tmda-pending-release)
  (local-set-key "d" 'tmda-pending-delete)
  (local-set-key "c" 'tmda-pending-clear-mark)
  (local-set-key " " 'tmda-pending-clear-mark)
  (local-set-key "\C-?" 'tmda-pending-backward-clear)
  (local-set-key "x" 'tmda-pending-apply-changes)
  (local-set-key "n" 'tmda-pending-next-msg)
  (local-set-key "p" 'tmda-pending-prev-msg)
  (local-set-key (kbd "C-r") 'tmda-pending-refresh-buffer))

(defun tmda-pending ()
  "Display a buffer for managing the TMDA pending queue."
  (interactive)
  (tmda-pending-refresh-buffer)
  (tmda-pending-setup-keys))

(defvar tmda-pending-count "*")

(defun tmda-pending-update-count ()
  "Function which updates the tmda-pending-count variable.
This is useful for viewing the number of pending messages in the modeline."
  (let ((count (string-to-number (shell-command-to-string
				  "tmda-pending -bT | wc -l"))))
    (setq tmda-pending-count (format "%d" count))))

;; What version of TMDA do we need?
(defvar tmda-major-ver-req 0)
(defvar tmda-minor-ver-req 58)

(defun tmda-check-version ()
  (let ((ver (shell-command-to-string "tmda-keygen --version")))
    (and (string-match "\\([0-9]+\\)\\.\\([0-9]+\\)" ver)
	 (let ((major (string-to-int (match-string 1 ver))))
	   (or (> major tmda-major-ver-req)
	       (and (= major tmda-major-ver-req)
		    (>= (string-to-int (match-string 2 ver))
			tmda-minor-ver-req)))))))

;; utility function to setup keybindings

(defun tmda-install-hooks ()
  "Install hooks, change settings to use all the functions contained
within this (tmda.el) module.  Please check before using."
  (if (not (tmda-check-version))
      (message
       (format "Your installed TMDA is not new enough, %d.%d required"
	       tmda-major-ver-req tmda-minor-ver-req))
    (require 'message)
    (define-key message-mode-map (kbd "C-c M-t s")
      'tmda-check-recipient-status)
    (define-key message-mode-map (kbd "C-c C-f T")
      'tmda-generate-header)
    (global-set-key (kbd "C-c M-t b") 'tmda-blacklist-at-point)
    (global-set-key (kbd "C-c M-t w") 'tmda-whitelist-at-point)
    (global-set-key (kbd "C-c M-t B") 'tmda-blacklist-wildcard-at-point)
    (global-set-key (kbd "C-c M-t W") 'tmda-whitelist-wildcard-at-point)
    (define-key gnus-summary-mode-map (kbd "C-c M-t b")
      'tmda-summary-blacklist-sender)
    (define-key gnus-summary-mode-map (kbd "C-c M-t w")
      'tmda-summary-whitelist-sender)
    (define-key gnus-summary-mode-map (kbd "C-c M-t B")
      'tmda-summary-blacklist-wildcard-sender)
    (define-key gnus-summary-mode-map (kbd "C-c M-t W")
      'tmda-summary-whitelist-wildcard-sender)
    (global-set-key (kbd "C-c M-t a") 'tmda-generate-address)
    (global-set-key (kbd "C-c M-t p") 'tmda-pending)))

(provide 'tmda)
