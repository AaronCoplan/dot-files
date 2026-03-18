;;; config.el -*- lexical-binding: t; -*-

;; Default to emacs-style keybindings in all buffers
(setq evil-default-state 'emacs)
(add-hook 'after-change-major-mode-hook 'evil-emacs-state)

;; Indentation settings
(setq-default c-basic-offset 8)
(add-hook 'java-mode-hook (lambda ()
                            (setq c-basic-offset 4)))
